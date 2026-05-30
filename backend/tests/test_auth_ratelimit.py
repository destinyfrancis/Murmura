"""Unit tests for auth rate limiter configuration."""

from __future__ import annotations

import pytest


@pytest.mark.unit
def test_rate_limiter_is_configured():
    """Auth router routes exist and limiter is importable."""
    from backend.app.api.auth import _limiter, router

    login_route = next(
        (r for r in router.routes if hasattr(r, "path") and r.path == "/auth/login"),
        None,
    )
    assert login_route is not None, "Login route must exist"
    assert _limiter is not None, "Rate limiter must be configured"


@pytest.mark.unit
def test_register_route_exists():
    """Register route is present on auth router."""
    from backend.app.api.auth import router

    register_route = next(
        (r for r in router.routes if hasattr(r, "path") and r.path == "/auth/register"),
        None,
    )
    assert register_route is not None, "Register route must exist"


@pytest.mark.unit
def test_limiter_uses_remote_address():
    """Rate limiter key function is remote-address based."""
    from slowapi.util import get_remote_address

    from backend.app.api.auth import _limiter

    assert _limiter._key_func is get_remote_address


@pytest.mark.asyncio
async def test_register_rate_limit_returns_429(rate_limited_client):
    for i in range(3):
        resp = await rate_limited_client.post(
            "/api/auth/register",
            json={"email": f"rl-register-{i}@example.com", "password": "password123"},
        )
        assert resp.status_code == 200

    resp = await rate_limited_client.post(
        "/api/auth/register",
        json={"email": "rl-register-over@example.com", "password": "password123"},
    )
    assert resp.status_code == 429
    assert "traceback" not in resp.text.lower()


@pytest.mark.asyncio
async def test_login_rate_limit_returns_429(rate_limited_client):
    for _ in range(5):
        resp = await rate_limited_client.post(
            "/api/auth/login",
            json={"email": "missing@example.com", "password": "password123"},
        )
        assert resp.status_code == 401

    resp = await rate_limited_client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "password123"},
    )
    assert resp.status_code == 429
    assert "traceback" not in resp.text.lower()


@pytest.mark.asyncio
async def test_report_generate_rate_limit_returns_429(monkeypatch, rate_limited_client):
    from backend.app.api.auth import _create_access_token, _hash_password
    from backend.app.services.report_agent import ReportAgent
    from backend.app.utils.db import get_db

    async def fake_generate_report(self, **kwargs):  # noqa: ANN001
        return {"report_id": "r1", "total_cost_usd": 0.0}

    monkeypatch.setattr(ReportAgent, "generate_report", fake_generate_report)
    user_id = "rate-limit-report-user"
    async with get_db() as db:
        await db.execute(
            "INSERT INTO users (id, email, password_hash, display_name, is_admin) VALUES (?, ?, ?, ?, 0)",
            (user_id, "rl-report@example.com", _hash_password("password123"), "Rate Limit"),
        )
        await db.execute(
            """INSERT INTO simulation_sessions
               (id, name, sim_mode, seed_text, scenario_type, graph_id, agent_count,
                round_count, llm_provider, llm_model, status, owner_id)
               VALUES ('sess-rate-limit', 'Rate Limit', 'kg_driven', 'seed', 'kg_driven',
                       'sess-rate-limit', 1, 1, 'openrouter', 'test-model', 'completed', ?)""",
            (user_id,),
        )
        await db.commit()

    payload = {"session_id": "sess-rate-limit", "report_type": "full"}
    headers = {"Authorization": f"Bearer {_create_access_token(user_id)}"}
    for _ in range(5):
        resp = await rate_limited_client.post("/api/report/generate", json=payload, headers=headers)
        assert resp.status_code == 200

    resp = await rate_limited_client.post("/api/report/generate", json=payload, headers=headers)
    assert resp.status_code == 429
    assert "traceback" not in resp.text.lower()

from __future__ import annotations

import json

import pytest

from backend.app.utils.db import get_db


async def _register(client, email: str, *, admin: bool = False) -> tuple[str, str]:
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    if admin:
        async with get_db() as db:
            await db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (data["user_id"],))
            await db.commit()
    return data["user_id"], data["token"]


async def _seed_session(session_id: str, owner_id: str | None) -> None:
    async with get_db() as db:
        await db.execute(
            """INSERT INTO simulation_sessions
               (id, name, sim_mode, seed_text, scenario_type, graph_id, agent_count,
                round_count, llm_provider, llm_model, status, current_round, owner_id, platforms)
               VALUES (?, ?, 'kg_driven', 'seed', 'kg_driven', ?, 1, 1,
                       'openrouter', 'test-model', 'created', 0, ?, ?)""",
            (session_id, session_id, session_id, owner_id, json.dumps({"twitter": True})),
        )
        await db.commit()


async def _seed_report(report_id: str, session_id: str, token: str | None = None) -> None:
    async with get_db() as db:
        await db.execute(
            """INSERT INTO reports
               (id, session_id, report_type, title, content_markdown, summary,
                key_findings, charts_data, share_token)
               VALUES (?, ?, 'full', 'Report', 'Body', 'Summary', '[]', '{}', ?)""",
            (report_id, session_id, token),
        )
        await db.commit()


async def _seed_report_content(report_id: str, session_id: str, content: str) -> None:
    async with get_db() as db:
        await db.execute(
            """INSERT INTO reports
               (id, session_id, report_type, title, content_markdown, summary,
                key_findings, charts_data)
               VALUES (?, ?, 'full', ?, ?, 'Summary', '[]', '{}')""",
            (report_id, session_id, "<img src=http://internal/title>", content),
        )
        await db.commit()


async def _seed_agent_profile(session_id: str, *, agent_id: int = 1) -> None:
    async with get_db() as db:
        await db.execute(
            """INSERT INTO agent_profiles
               (id, session_id, agent_type, age, sex, district, occupation,
                income_bracket, education_level, marital_status, housing_type,
                openness, conscientiousness, extraversion, agreeableness, neuroticism,
                monthly_income, savings, oasis_persona, oasis_username)
               VALUES (?, ?, 'person', 33, 'N/A', 'Central', 'Analyst',
                       'N/A', 'N/A', 'N/A', 'N/A',
                       0.5, 0.5, 0.5, 0.5, 0.5,
                       0, 0, 'Persona from OASIS', 'persona_user')""",
            (agent_id, session_id),
        )
        await db.commit()


@pytest.mark.asyncio
async def test_session_list_filters_by_owner_and_admin(test_client) -> None:
    user_a, token_a = await _register(test_client, "owner-a@example.com")
    user_b, _token_b = await _register(test_client, "owner-b@example.com")
    _admin, admin_token = await _register(test_client, "owner-admin@example.com", admin=True)

    await _seed_session("sess-a", user_a)
    await _seed_session("sess-b", user_b)
    await _seed_session("sess-demo", None)

    anon_resp = await test_client.get("/api/simulation/sessions")
    assert anon_resp.status_code == 200
    assert {s["id"] for s in anon_resp.json()["data"]["sessions"]} == {"sess-demo"}

    user_resp = await test_client.get(
        "/api/simulation/sessions",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert user_resp.status_code == 200
    assert {s["id"] for s in user_resp.json()["data"]["sessions"]} == {"sess-a", "sess-demo"}

    admin_resp = await test_client.get(
        "/api/simulation/sessions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_resp.status_code == 200
    assert {s["id"] for s in admin_resp.json()["data"]["sessions"]} == {"sess-a", "sess-b", "sess-demo"}


@pytest.mark.asyncio
async def test_owned_session_status_blocks_other_users_and_anonymous(test_client) -> None:
    user_a, token_a = await _register(test_client, "status-a@example.com")
    _user_b, token_b = await _register(test_client, "status-b@example.com")
    await _seed_session("status-owned", user_a)

    anon_resp = await test_client.get("/api/simulation/status-owned/status")
    assert anon_resp.status_code == 401

    other_resp = await test_client.get(
        "/api/simulation/status-owned/status",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert other_resp.status_code == 403

    owner_resp = await test_client.get(
        "/api/simulation/status-owned/status",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert owner_resp.status_code == 200


@pytest.mark.asyncio
async def test_simulation_interview_router_blocks_other_users_and_anonymous(test_client) -> None:
    user_a, _token_a = await _register(test_client, "interview-route-a@example.com")
    _user_b, token_b = await _register(test_client, "interview-route-b@example.com")
    session_id = "deadbeef-dead-beef-dead-beefdeadbeef"
    await _seed_session(session_id, user_a)

    anon_resp = await test_client.post(
        f"/api/simulation/{session_id}/agents/1/interview",
        json={"query": "Hello"},
    )
    assert anon_resp.status_code == 401

    other_resp = await test_client.post(
        f"/api/simulation/{session_id}/agents/1/interview",
        json={"query": "Hello"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert other_resp.status_code == 403


@pytest.mark.asyncio
async def test_report_private_endpoints_require_report_owner_or_admin(test_client) -> None:
    user_a, token_a = await _register(test_client, "report-a@example.com")
    _user_b, token_b = await _register(test_client, "report-b@example.com")
    _admin, admin_token = await _register(test_client, "report-admin@example.com", admin=True)
    await _seed_session("report-session-a", user_a)
    await _seed_report("report-a", "report-session-a", token="public-token-a")

    anon_private = await test_client.get("/api/report/report-a")
    assert anon_private.status_code == 401

    other_private = await test_client.get(
        "/api/report/report-a",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert other_private.status_code == 403

    owner_private = await test_client.get(
        "/api/report/report-a",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert owner_private.status_code == 200

    admin_private = await test_client.get(
        "/api/report/report-a",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_private.status_code == 200

    public_resp = await test_client.get("/api/report/public/public-token-a")
    assert public_resp.status_code == 200


@pytest.mark.asyncio
async def test_report_pdf_escapes_html_and_blocks_remote_fetch(monkeypatch, test_client) -> None:
    weasyprint = pytest.importorskip("weasyprint")

    user_id, token = await _register(test_client, "pdf-owner@example.com")
    await _seed_session("pdf-session", user_id)
    await _seed_report_content(
        "pdf-report",
        "pdf-session",
        "# Title\n<script>alert(1)</script>\n<img src=http://internal.example/secret>",
    )

    captured: dict[str, object] = {}

    class FakeHTML:
        def __init__(self, string: str, url_fetcher=None) -> None:
            captured["html"] = string
            captured["url_fetcher"] = url_fetcher

        def write_pdf(self) -> bytes:
            fetcher = captured["url_fetcher"]
            assert callable(fetcher)
            with pytest.raises(ValueError):
                fetcher("http://internal.example/secret")
            captured["blocked"] = True
            return b"%PDF-1.4"

    monkeypatch.setattr(weasyprint, "HTML", FakeHTML)

    resp = await test_client.get(
        "/api/report/pdf-report/pdf",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    html = str(captured["html"])
    assert "<script" not in html.lower()
    assert "<img" not in html.lower()
    assert "http://internal.example/secret" in html
    assert captured["blocked"] is True


@pytest.mark.asyncio
async def test_report_interview_uses_oasis_username_and_persona(monkeypatch, test_client) -> None:
    from backend.app.services import report_agent

    user_id, token = await _register(test_client, "interview-owner@example.com")
    await _seed_session("interview-session", user_id)
    await _seed_agent_profile("interview-session")

    captured: dict[str, object] = {}

    async def fake_call_llm(messages, system_prompt):  # noqa: ANN001
        captured["messages"] = messages
        captured["system_prompt"] = system_prompt
        return "persona answer"

    monkeypatch.setattr(report_agent, "_call_llm", fake_call_llm)

    resp = await test_client.post(
        "/api/report/interview",
        json={"session_id": "interview-session", "agent_id": "persona_user", "question": "Who are you?"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    system_prompt = str(captured["system_prompt"])
    assert "persona_user" in system_prompt
    assert "Persona from OASIS" in system_prompt

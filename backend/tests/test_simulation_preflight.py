from __future__ import annotations

import pytest

from backend.app.services import runtime_settings


@pytest.fixture(autouse=True)
def _clear_runtime_settings(monkeypatch):
    runtime_settings._store.clear()
    monkeypatch.delenv("MURMURA_PREFLIGHT_LIVE_MODEL_CHECK", raising=False)
    yield
    runtime_settings._store.clear()


def _oasis_available(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.app.services.oasis_compatibility.get_capabilities",
        lambda: {
            "simulation": True,
            "simulation_available": True,
            "reason": "",
            "python_path": ".venv311/bin/python",
            "oasis_importable": True,
        },
    )


@pytest.mark.asyncio
async def test_preflight_valid_static_model_ready(monkeypatch):
    from backend.app.services.simulation_preflight import SimulationPreflightService

    _oasis_available(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    report = await SimulationPreflightService().run(
        {
            "seed_text": "A policy shock ripples through public debate.",
            "llm_provider": "openrouter",
            "llm_model": "deepseek/deepseek-v3.2",
            "agent_count": 10,
            "round_count": 1,
            "platforms": {"twitter": True},
        }
    )

    assert report["ready"] is True
    assert report["model_check"]["api_key_present"] is True
    assert report["cost_estimate"]["estimated_cost_usd"] >= 0
    assert report["time_config"]["minutes_per_round"] > 0


@pytest.mark.asyncio
async def test_preflight_blocks_missing_api_key(monkeypatch):
    from backend.app.services.simulation_preflight import SimulationPreflightService

    _oasis_available(monkeypatch)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    report = await SimulationPreflightService().run(
        {
            "seed_text": "seed",
            "llm_provider": "openrouter",
            "llm_model": "deepseek/deepseek-v3.2",
            "agent_count": 10,
            "round_count": 1,
            "platforms": {"twitter": True},
        }
    )

    assert report["ready"] is False
    assert {e["code"] for e in report["blocking_errors"]} == {"missing_api_key"}


@pytest.mark.asyncio
async def test_preflight_blocks_known_bad_fireworks_model(monkeypatch):
    from backend.app.services.simulation_preflight import SimulationPreflightService

    _oasis_available(monkeypatch)
    monkeypatch.setenv("FIREWORKS_API_KEY", "fw-test")

    report = await SimulationPreflightService().run(
        {
            "seed_text": "seed",
            "llm_provider": "fireworks",
            "llm_model": "accounts/fireworks/models/deepseek-v3p2",
            "agent_count": 10,
            "round_count": 1,
            "platforms": {"twitter": True},
        }
    )

    assert report["ready"] is False
    assert report["model_check"]["status"] == "known_bad_model"


@pytest.mark.asyncio
async def test_preflight_ignores_known_bad_runtime_model_for_provider_default(monkeypatch):
    from backend.app.services.simulation_preflight import SimulationPreflightService

    _oasis_available(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    runtime_settings.set_override("agent_llm_model", "accounts/fireworks/models/deepseek-v3p2")

    report = await SimulationPreflightService().run(
        {
            "seed_text": "seed",
            "llm_provider": "openrouter",
            "agent_count": 10,
            "round_count": 1,
            "platforms": {"twitter": True},
        }
    )

    assert report["ready"] is True
    assert report["model_check"]["model"] == "deepseek/deepseek-v3.2"


@pytest.mark.asyncio
async def test_preflight_falls_back_from_known_bad_fireworks_env_model(monkeypatch):
    from backend.app.services.simulation_preflight import SimulationPreflightService

    _oasis_available(monkeypatch)
    monkeypatch.setenv("FIREWORKS_API_KEY", "fw-test")
    monkeypatch.setenv("AGENT_LLM_PROVIDER", "fireworks")
    monkeypatch.setenv("AGENT_LLM_MODEL", "accounts/fireworks/models/deepseek/deepseek-v3.2")

    report = await SimulationPreflightService().run(
        {
            "seed_text": "seed",
            "agent_count": 10,
            "round_count": 1,
            "platforms": {"twitter": True},
        }
    )

    assert report["ready"] is True
    assert report["model_check"]["provider"] == "fireworks"
    assert report["model_check"]["model"] == "accounts/fireworks/models/minimax-m2p5"
    assert "model_fallback_applied" in {warning["code"] for warning in report["warnings"]}


def test_preflight_falls_back_from_cross_provider_session_default():
    from backend.app.services.simulation_preflight import SimulationPreflightService

    warnings: list[dict] = []
    provider, model = SimulationPreflightService()._resolve_provider_model(
        {
            "llm_provider": "fireworks",
            "llm_model": "deepseek/deepseek-v3.2",
            "_request_model_explicit": False,
            "_config_model_explicit": False,
        },
        warnings,
    )

    assert provider == "fireworks"
    assert model == "accounts/fireworks/models/minimax-m2p5"
    assert "model_fallback_applied" in {warning["code"] for warning in warnings}


@pytest.mark.asyncio
async def test_preflight_blocks_oasis_unavailable(monkeypatch):
    from backend.app.services.simulation_preflight import SimulationPreflightService

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.setattr(
        "backend.app.services.oasis_compatibility.get_capabilities",
        lambda: {"simulation_available": False, "reason": "python_312", "oasis_importable": False},
    )

    report = await SimulationPreflightService().run(
        {
            "seed_text": "seed",
            "llm_provider": "openrouter",
            "llm_model": "deepseek/deepseek-v3.2",
            "agent_count": 10,
            "round_count": 1,
            "platforms": {"twitter": True},
        }
    )

    assert report["ready"] is False
    assert "simulation_engine_unavailable" in {e["code"] for e in report["blocking_errors"]}


@pytest.mark.asyncio
async def test_preflight_endpoint_does_not_enqueue_jobs(monkeypatch, test_client):
    from backend.app.utils.db import get_db

    _oasis_available(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    resp = await test_client.post(
        "/api/simulation/preflight",
        json={
            "seed_text": "seed",
            "llm_provider": "openrouter",
            "llm_model": "deepseek/deepseek-v3.2",
            "agent_count": 10,
            "round_count": 1,
            "platforms": {"twitter": True},
        },
    )

    assert resp.status_code == 200
    assert resp.json()["data"]["ready"] is True
    async with get_db() as db:
        row = await (await db.execute("SELECT COUNT(*) AS c FROM simulation_jobs")).fetchone()
    assert row["c"] == 0


@pytest.mark.asyncio
async def test_preflight_blocks_cost_hard_cap(monkeypatch):
    from backend.app.services.simulation_preflight import SimulationPreflightService

    _oasis_available(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.setenv("SESSION_COST_HARD_CAP_USD", "0.01")

    report = await SimulationPreflightService().run(
        {
            "seed_text": "seed",
            "llm_provider": "openrouter",
            "llm_model": "deepseek/deepseek-v3.2",
            "agent_count": 300,
            "round_count": 20,
            "platforms": {"twitter": True},
        }
    )

    assert "cost_exceeds_hard_cap" in {e["code"] for e in report["blocking_errors"]}

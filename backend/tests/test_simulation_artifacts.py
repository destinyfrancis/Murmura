from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import aiosqlite
import pytest


async def _insert_session(db, session_id: str, *, status: str = "completed", error: str = "") -> None:
    await db.execute(
        """
        INSERT INTO simulation_sessions
            (id, name, sim_mode, seed_text, scenario_type, graph_id,
             agent_count, round_count, llm_provider, llm_model, oasis_db_path,
             status, estimated_cost_usd, config_json, created_at, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
        """,
        (
            session_id,
            "Artifact test",
            "hk_demographic",
            "seed",
            "property",
            "graph-1",
            10,
            1,
            "openrouter",
            "test-model",
            f"data/sessions/{session_id}/oasis.db",
            status,
            0,
            json.dumps({"agent_csv_path": f"data/sessions/{session_id}/agents.csv"}),
            error,
        ),
    )


@pytest.mark.asyncio
async def test_artifact_endpoint_hides_secrets_and_returns_counts(test_client):
    from backend.app.services.simulation_helpers import _PROJECT_ROOT
    from backend.app.utils.db import get_db

    session_id = "artifact-secret-test"
    session_dir = _PROJECT_ROOT / "data" / "sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "sim.log").write_text(
        "ERROR Authorization: Bearer sk-liveSECRET123456789 failed\n",
        encoding="utf-8",
    )

    async with get_db() as db:
        await _insert_session(db, session_id, status="failed", error="api_key=sk-liveSECRET123456789 failed")
        await db.execute(
            """
            INSERT INTO agent_profiles
                (id, session_id, agent_type, age, sex, district, occupation,
                 income_bracket, education_level, marital_status, housing_type,
                 openness, conscientiousness, extraversion, agreeableness, neuroticism,
                 monthly_income, savings, oasis_persona, oasis_username)
            VALUES
                (1, ?, 'citizen', 35, 'M', 'Central', 'Analyst',
                 'middle', 'tertiary', 'single', 'private',
                 0.5, 0.5, 0.5, 0.5, 0.5,
                 25000, 100000, 'test persona', 'agent_1')
            """,
            (session_id,),
        )
        await db.execute(
            """
            INSERT INTO simulation_actions
                (session_id, round_number, agent_id, oasis_username, action_type, platform, content)
            VALUES (?, 1, 1, 'agent_1', 'post', 'twitter', 'hello')
            """,
            (session_id,),
        )
        await db.execute(
            "INSERT INTO simulation_jobs (session_id, status, error_message) VALUES (?, 'failed', ?)",
            (session_id, "model call failed with sk-liveSECRET123456789"),
        )
        await db.commit()

    res = await test_client.get(f"/api/simulation/{session_id}/artifacts")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["counts"]["agents"] == 1
    assert data["counts"]["actions"] == 1
    assert data["counts"]["posts"] == 1
    assert data["failure_reason"] == "model_call_failed"
    assert data["retryable"] is True
    assert "Settings" in data["recommended_action"]
    assert data["normalized_failure"]["code"] == "model_call_failed"
    serialized = json.dumps(data)
    assert "sk-liveSECRET" not in serialized
    assert data["errors"][0]["code"] in {"model_call_failed", "oasis_runtime_error"}


@pytest.mark.asyncio
async def test_public_workflow_fails_when_oasis_unavailable(test_db_path, monkeypatch):
    import backend.app.config as config_mod
    from backend.app.services import workflow_runner as workflow_mod
    from backend.app.services.workflow_runner import WorkflowRunner

    schema_path = Path(__file__).resolve().parent.parent / "database" / "schema.sql"
    async with aiosqlite.connect(test_db_path) as db:
        await db.executescript(schema_path.read_text(encoding="utf-8"))
        await db.commit()

    with monkeypatch.context() as m:
        m.setenv("DATABASE_PATH", test_db_path)
        m.delenv("MURMURA_INTERNAL_DEGRADED", raising=False)
        m.setattr(config_mod, "_settings", config_mod.Settings())
        m.setattr(
            workflow_mod.ZeroConfigService,
            "prepare",
            AsyncMock(return_value=SimpleNamespace(mode="hk_demographic", domain_pack_id="hk_city")),
        )
        m.setattr(
            workflow_mod.ZeroConfigService,
            "infer_time_config",
            AsyncMock(return_value=SimpleNamespace(to_dict=lambda: {})),
        )
        m.setattr(
            workflow_mod.GraphBuilderService,
            "build_graph_from_seed",
            AsyncMock(return_value={"graph_id": "graph-1", "node_count": 2, "edge_count": 1}),
        )

        class FakeManager:
            async def create_session(self, *_args, **_kwargs):
                return {"session_id": "workflow-oasis-down"}

        m.setattr(workflow_mod, "get_simulation_manager", lambda: FakeManager())
        m.setattr(workflow_mod, "generate_agents", AsyncMock(return_value=([object()], "agents.csv")))
        m.setattr("backend.app.services.oasis_compatibility.get_capabilities", lambda: {"simulation_available": False, "reason": "python_312"})

        runner = WorkflowRunner()
        workflow = await runner.create_workflow(seed_text="seed", preset="fast")
        await runner.run(workflow["workflow_id"])
        state = await runner.get_workflow(workflow["workflow_id"])

    assert state["status"] == "failed"
    assert state["artifacts"]["failure_reason"] == "oasis_runtime_error"
    assert any(event["event_type"] == "simulation_failed" for event in state["events"])


@pytest.mark.asyncio
async def test_zero_effective_actions_count_is_explicit_failure_signal(test_client):
    from backend.app.services.simulation_artifacts import classify_failure, count_effective_actions
    from backend.app.utils.db import get_db

    session_id = "zero-actions-test"
    async with get_db() as db:
        await _insert_session(db, session_id, status="failed", error="no_effective_actions: OASIS completed")
        await db.commit()

    assert await count_effective_actions(session_id) == 0
    assert classify_failure("no_effective_actions: OASIS completed") == "no_effective_actions"
    assert classify_failure("round_timeout: simulation monitor timed out") == "round_timeout"
    assert classify_failure("Model not found, inaccessible, and/or not deployed") == "model_call_failed"


@pytest.mark.asyncio
async def test_refresh_actions_do_not_count_as_effective(test_client):
    from backend.app.services.simulation_artifacts import count_effective_actions
    from backend.app.utils.db import get_db

    session_id = "refresh-only-test"
    async with get_db() as db:
        await _insert_session(db, session_id)
        await db.execute(
            """
            INSERT INTO simulation_actions
                (session_id, round_number, agent_id, oasis_username, action_type, platform, content)
            VALUES
                (?, 1, 1, 'agent_1', 'refresh', 'twitter', '{}'),
                (?, 1, 1, 'agent_1', 'do_nothing', 'twitter', '')
            """,
            (session_id, session_id),
        )
        await db.commit()

    assert await count_effective_actions(session_id) == 0


@pytest.mark.asyncio
async def test_empty_errors_summary_is_not_reported_as_failure(test_client):
    from backend.app.services.simulation_artifacts import collect_simulation_artifacts
    from backend.app.services.simulation_helpers import _PROJECT_ROOT
    from backend.app.utils.db import get_db

    session_id = "empty-errors-summary-test"
    session_dir = _PROJECT_ROOT / "data" / "sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "sim.log").write_text(
        "INFO parallel_simulation: Parallel simulation finished. Results: {}, Errors: {}\n",
        encoding="utf-8",
    )

    async with get_db() as db:
        await _insert_session(db, session_id)
        await db.commit()

    data = await collect_simulation_artifacts(session_id)
    assert data["counts"]["errors"] == 0
    assert data["errors"] == []

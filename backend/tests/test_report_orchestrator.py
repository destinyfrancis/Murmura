# backend/tests/test_report_orchestrator.py
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_report_generate_request_has_scenario_question():
    from backend.app.models.request import ReportGenerateRequest

    req = ReportGenerateRequest(session_id="s1")
    assert req.scenario_question is None  # optional with default None


def test_report_generate_request_accepts_scenario_question():
    from backend.app.models.request import ReportGenerateRequest

    req = ReportGenerateRequest(session_id="s1", scenario_question="如果X發生，輿情會怎樣？")
    assert req.scenario_question == "如果X發生，輿情會怎樣？"


def test_orchestrator_outline_parses_chapters():
    """ReportOrchestrator._parse_outline extracts chapters list."""
    from backend.app.services.report_orchestrator import ReportOrchestrator

    orch = ReportOrchestrator.__new__(ReportOrchestrator)
    raw = '{"chapters": [{"title": "輿情遷移", "thesis": "議題將升級", "suggested_tools": ["insight_forge"]}]}'
    chapters = orch._parse_outline(raw)
    assert len(chapters) == 1
    assert chapters[0]["title"] == "輿情遷移"


def test_orchestrator_outline_handles_malformed_json():
    from backend.app.services.report_orchestrator import ReportOrchestrator

    orch = ReportOrchestrator.__new__(ReportOrchestrator)
    # Should not raise — returns empty list or fallback
    result = orch._parse_outline("not json at all")
    assert isinstance(result, list)


def test_orchestrator_outline_handles_missing_chapters_key():
    from backend.app.services.report_orchestrator import ReportOrchestrator

    orch = ReportOrchestrator.__new__(ReportOrchestrator)
    result = orch._parse_outline('{"something_else": []}')
    assert result == []


def test_orchestrator_outline_handles_trailing_prose():
    """Balanced-brace parser handles trailing prose after JSON without dropping chapters."""
    from backend.app.services.report_orchestrator import ReportOrchestrator

    orch = ReportOrchestrator.__new__(ReportOrchestrator)
    raw = (
        '{"chapters": [{"title": "A", "thesis": "T", "suggested_tools": []}, '
        '{"title": "B", "thesis": "T2", "suggested_tools": []}]} '
        "Some trailing prose here."
    )
    chapters = orch._parse_outline(raw)
    assert len(chapters) == 2
    assert chapters[1]["title"] == "B"


@pytest.mark.asyncio
async def test_orchestrator_session_meta_uses_existing_schema(tmp_path):
    """_get_session_meta must not query nonexistent simulation_sessions.preset."""
    from contextlib import asynccontextmanager

    import aiosqlite

    from backend.app.services.report_orchestrator import ReportOrchestrator

    db_path = tmp_path / "orchestrator.db"
    schema_path = Path(__file__).parent.parent / "database" / "schema.sql"
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript(schema_path.read_text(encoding="utf-8"))
        await db.execute(
            """INSERT INTO simulation_sessions
               (id, name, sim_mode, seed_text, agent_count, round_count, llm_provider, config_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "sess-meta",
                "test-session",
                "kg_driven",
                "long seed",
                12,
                7,
                "test",
                json.dumps({"time_config": {"round_label_unit": "day"}}),
            ),
        )
        await db.commit()

    @asynccontextmanager
    async def _patched_get_db():
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row
            yield conn

    orch = ReportOrchestrator.__new__(ReportOrchestrator)
    with patch("backend.app.services.report_orchestrator.get_db", _patched_get_db):
        meta = await orch._get_session_meta("sess-meta")

    assert meta["sim_mode"] == "kg_driven"
    assert meta["agent_count"] == 12
    assert meta["round_count"] == 7
    assert meta["time_config"] == {"round_label_unit": "day"}


@pytest.mark.asyncio
async def test_orchestrator_generate_returns_markdown():
    """generate() returns assembled markdown string."""
    from backend.app.services.report_orchestrator import ReportOrchestrator

    def _resp(text: str) -> MagicMock:
        r = MagicMock()
        r.content = text
        return r

    mock_llm = MagicMock()
    # Phase 1: outline response
    # Phase 2: section generation — tool calls then final answer
    mock_llm.chat = AsyncMock(
        side_effect=[
            _resp('{"chapters": [{"title": "趨勢預測", "thesis": "將會升級", "suggested_tools": ["insight_forge"]}]}'),
            _resp('<tool_call>{"name": "insight_forge", "parameters": {"query": "test"}}</tool_call>'),
            _resp('<tool_call>{"name": "interview_agents", "parameters": {}}</tool_call>'),
            _resp('<tool_call>{"name": "get_sentiment_timeline", "parameters": {}}</tool_call>'),
            _resp("Final Answer: This is the section content."),
        ]
    )

    async def mock_tool(name, params):
        return f"mock result from {name}"

    orch = ReportOrchestrator(llm_client=mock_llm)
    # Mock _get_session_meta to avoid DB
    orch._get_session_meta = AsyncMock(return_value={"sim_mode": "kg_driven", "agent_count": 100, "round_count": 15})

    result = await orch.generate(
        session_id="sess1",
        scenario_question="如果X發生，輿情會怎樣？",
        report_type="full",
        tool_handler=mock_tool,
        tool_names=["insight_forge", "interview_agents", "get_sentiment_timeline"],
    )
    assert "# 預測報告" in result
    assert "趨勢預測" in result

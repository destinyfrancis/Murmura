"""Tests for deterministic grounded reports."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest

from backend.app.services.grounded_report import GroundedReportBuilder


async def _seed_report_db(db, session_id: str) -> None:
    await db.execute(
        """
        INSERT INTO simulation_sessions
            (id, name, sim_mode, seed_text, scenario_type, scenario_question,
             agent_count, round_count, llm_provider, llm_model, oasis_db_path,
             current_round)
        VALUES (?, 'Report Test', 'kg_driven', '新產品推出', 'market',
                '新產品推出會點?', 2, 3, 'test', 'test-model', '', 2)
        """,
        (session_id,),
    )
    await db.executemany(
        """
        INSERT INTO kg_nodes
            (id, session_id, entity_type, title, description, properties,
             confidence_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("product", session_id, "Product", "新產品", "launch", "{}", 0.9),
            ("customer", session_id, "Stakeholder", "早期用戶", "customers", "{}", 0.8),
            (
                "hidden_reg",
                session_id,
                "Institution",
                "監管者",
                "審查宣稱",
                '{"source":"implicit_discovery","evidence_phrase":"產品宣稱","include_in_simulation":true}',
                0.7,
            ),
        ],
    )
    await db.execute(
        """
        INSERT INTO kg_edges
            (session_id, source_id, target_id, relation_type, description,
             source_text, evidence_span, confidence_score)
        VALUES (?, 'product', 'customer', 'AFFECTS', '產品影響早期用戶',
                '新產品推出影響早期用戶', '{"start":0,"end":10}', 0.85)
        """,
        (session_id,),
    )
    await db.execute(
        """
        INSERT INTO simulation_actions
            (session_id, round_number, agent_id, oasis_username, action_type,
             platform, content, sentiment, topics)
        VALUES (?, 2, 1, 'alice', 'post', 'twitter',
                '我支持新產品但擔心宣稱太誇張', 'positive', '["新產品"]')
        """,
        (session_id,),
    )
    await db.commit()


@pytest.mark.asyncio
async def test_grounded_market_report_contains_standard_sections_and_evidence(test_db):
    session_id = "grounded_report"
    await _seed_report_db(test_db, session_id)

    @asynccontextmanager
    async def _mock_get_db():
        yield test_db

    with (
        patch("backend.app.services.grounded_report.get_db", _mock_get_db),
        patch("backend.app.services.graph_rag_query.get_db", _mock_get_db),
    ):
        bundle = await GroundedReportBuilder().build(session_id, "market_launch_forecast")

    report = bundle.to_report_dict()
    content = report["content_markdown"]
    assert "## Executive Verdict" in content
    assert "## Evidence Appendix" in content
    assert "observed simulation results" in content
    assert "kg_edges:" in content
    assert report["charts_data"]["evidence_bundle"]
    assert report["key_findings"]

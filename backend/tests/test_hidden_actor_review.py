"""Tests for evidence-linked hidden actors and simulation filtering."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.services.implicit_stakeholder_service import ImplicitStakeholderService
from backend.app.services.kg_agent_factory import KGAgentFactory


async def _insert_session(db, session_id: str) -> None:
    await db.execute(
        """
        INSERT INTO simulation_sessions
            (id, name, sim_mode, seed_text, scenario_type, agent_count,
             round_count, llm_provider, llm_model, oasis_db_path)
        VALUES (?, 'Hidden Actor Test', 'kg_driven', 'seed', 'market',
                2, 3, 'test', 'test-model', '')
        """,
        (session_id,),
    )


@pytest.mark.asyncio
async def test_hidden_actor_requires_evidence_and_persists_implied_by_edge(test_db):
    session_id = "hidden_actor_graph"
    await _insert_session(test_db, session_id)
    await test_db.execute(
        """
        INSERT INTO kg_nodes
            (id, session_id, entity_type, title, description, properties)
        VALUES ('explicit_company', ?, 'Company', 'Acme', 'Explicit actor', '{}')
        """,
        (session_id,),
    )
    await test_db.commit()

    llm = MagicMock()
    llm.chat_json = AsyncMock(
        return_value={
            "implied_actors": [
                {
                    "id": "regulator",
                    "name": "監管機構",
                    "entity_type": "Institution",
                    "role": "審查產品宣稱",
                    "relevance_reason": "產品宣稱可能受監管審查影響。",
                    "why_missing": "種子只提到產品推出，未點名監管者。",
                    "evidence_phrase": "產品推出及市場宣稱",
                    "inferred_role": "評估是否介入或發警告。",
                    "confidence": 0.74,
                },
                {
                    "id": "unsupported",
                    "name": "無證據角色",
                    "entity_type": "Organization",
                    "role": "不應加入",
                    "relevance_reason": "",
                    "evidence_phrase": "",
                },
            ]
        }
    )

    @asynccontextmanager
    async def _mock_get_db():
        yield test_db

    with patch("backend.app.services.implicit_stakeholder_service.get_db", _mock_get_db):
        result = await ImplicitStakeholderService(llm_client=llm).discover(
            session_id,
            "Acme 正準備產品推出及市場宣稱。",
            [{"id": "explicit_company", "title": "Acme", "entity_type": "Company"}],
        )

    assert result.nodes_added == 1

    node = await (
        await test_db.execute(
            "SELECT id, properties, confidence_score FROM kg_nodes WHERE session_id = ? AND title = '監管機構'",
            (session_id,),
        )
    ).fetchone()
    assert node is not None
    assert '"include_in_simulation": true' in node["properties"]
    assert node["confidence_score"] == pytest.approx(0.74)

    edge = await (
        await test_db.execute(
            "SELECT relation_type, source_text FROM kg_edges WHERE session_id = ? AND source_id = ?",
            (session_id, node["id"]),
        )
    ).fetchone()
    assert edge is not None
    assert edge["relation_type"] == "IMPLIED_BY"
    assert edge["source_text"] == "產品推出及市場宣稱"


def test_kg_agent_factory_skips_hidden_actors_excluded_by_review():
    nodes = [
        {"id": "n1", "label": "Visible Company", "entity_type": "Company", "properties": "{}"},
        {
            "id": "n2",
            "label": "Rejected Regulator",
            "entity_type": "Institution",
            "properties": '{"source":"implicit_discovery","include_in_simulation":false}',
        },
    ]

    result = KGAgentFactory._heuristic_filter(nodes)
    assert [node["id"] for node in result] == ["n1"]

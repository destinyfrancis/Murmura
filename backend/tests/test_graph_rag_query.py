"""Tests for structured GraphRAG query retrieval."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest

from backend.app.services.graph_rag_query import GraphRAGQueryService


async def _seed_session(db, session_id: str) -> None:
    await db.execute(
        """
        INSERT INTO simulation_sessions
            (id, name, sim_mode, seed_text, scenario_type, agent_count,
             round_count, llm_provider, llm_model, oasis_db_path)
        VALUES (?, 'GraphRAG Query Test', 'kg_driven', 'seed', 'market',
                2, 3, 'test', 'test-model', '')
        """,
        (session_id,),
    )


async def _seed_graph(db, session_id: str) -> None:
    await db.executemany(
        """
        INSERT INTO kg_nodes
            (id, session_id, entity_type, title, description, properties,
             layer_type, confidence_score)
        VALUES (?, ?, ?, ?, ?, '{}', ?, ?)
        """,
        [
            ("n_product", session_id, "Product", "新產品", "AI launch product", "truth", 0.95),
            ("n_customer", session_id, "Stakeholder", "早期用戶", "customers", "truth", 0.9),
            ("n_competitor", session_id, "Organization", "競爭對手", "rival company", "truth", 0.88),
        ],
    )
    await db.executemany(
        """
        INSERT INTO kg_edges
            (session_id, source_id, target_id, relation_type, description,
             source_text, evidence_span, weight, round_number,
             layer_type, confidence_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                session_id,
                "n_product",
                "n_customer",
                "AFFECTS",
                "新產品影響早期用戶採納",
                "Brief says early users are affected by the product launch.",
                '{"start": 0, "end": 24}',
                0.8,
                0,
                "truth",
                0.9,
            ),
            (
                session_id,
                "n_customer",
                "n_competitor",
                "RESPONDS_TO",
                "競爭對手回應用戶流失",
                "Simulation shows competitors reacting to customer movement.",
                '{"round": 2}',
                0.7,
                2,
                "belief",
                0.72,
            ),
        ],
    )
    await db.commit()


@pytest.mark.asyncio
async def test_query_returns_two_hop_subgraph_and_evidence(test_db):
    session_id = "graph_rag_query"
    await _seed_session(test_db, session_id)
    await _seed_graph(test_db, session_id)

    @asynccontextmanager
    async def _mock_get_db():
        yield test_db

    with patch("backend.app.services.graph_rag_query.get_db", _mock_get_db):
        result = await GraphRAGQueryService().query(session_id, "新產品", hops=2)

    data = result.to_dict()
    assert data["mode"] == "graph"
    assert {n["id"] for n in data["nodes"]} == {"n_product", "n_customer", "n_competitor"}
    assert len(data["edges"]) == 2
    assert data["evidence"][0]["evidence_id"].startswith("kg_edges:")
    assert data["confidence"] > 0.5


@pytest.mark.asyncio
async def test_query_strict_no_match_does_not_keyword_fallback(test_db):
    session_id = "graph_rag_strict"
    await _seed_session(test_db, session_id)
    await _seed_graph(test_db, session_id)

    @asynccontextmanager
    async def _mock_get_db():
        yield test_db

    with patch("backend.app.services.graph_rag_query.get_db", _mock_get_db):
        result = await GraphRAGQueryService().query(session_id, "不存在", strict=True)

    assert result.mode == "strict_graph_no_match"
    assert result.nodes == ()
    assert result.evidence == ()


@pytest.mark.asyncio
async def test_query_degraded_keyword_search_is_explicit(test_db):
    session_id = "graph_rag_degraded"
    await _seed_session(test_db, session_id)
    await test_db.execute(
        """
        INSERT INTO simulation_actions
            (session_id, round_number, agent_id, oasis_username, action_type,
             platform, content, sentiment, topics)
        VALUES (?, 1, 1, 'alice', 'post', 'twitter',
                '大家討論監管風險', 'neutral', '["監管"]')
        """,
        (session_id,),
    )
    await test_db.commit()

    @asynccontextmanager
    async def _mock_get_db():
        yield test_db

    with patch("backend.app.services.graph_rag_query.get_db", _mock_get_db):
        result = await GraphRAGQueryService().query(session_id, "監管", strict=False)

    assert result.mode == "degraded_keyword_search"
    assert result.evidence
    assert result.evidence[0]["source"] == "simulation_actions"


@pytest.mark.asyncio
async def test_paths_returns_shortest_relation_chain(test_db):
    session_id = "graph_rag_path"
    await _seed_session(test_db, session_id)
    await _seed_graph(test_db, session_id)

    @asynccontextmanager
    async def _mock_get_db():
        yield test_db

    with patch("backend.app.services.graph_rag_query.get_db", _mock_get_db):
        paths = await GraphRAGQueryService().paths(session_id, "n_product", "n_competitor", max_hops=3)

    assert paths
    assert paths[0]["node_ids"] == ["n_product", "n_customer", "n_competitor"]
    assert paths[0]["relations"] == ["AFFECTS", "RESPONDS_TO"]

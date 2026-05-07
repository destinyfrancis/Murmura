"""Regression tests for the deterministic Stage 6 memory/KG update loop."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest

from backend.app.services.simulation_memory_graph_loop import SimulationMemoryGraphLoop


async def _insert_session(db, session_id: str = "sess_stage6") -> None:
    await db.execute(
        """
        INSERT INTO simulation_sessions
            (id, name, sim_mode, seed_text, scenario_type, agent_count,
             round_count, llm_provider, llm_model, oasis_db_path)
        VALUES (?, 'Stage 6 Test', 'kg_driven', 'seed', 'market',
                1, 3, 'test', 'test-model', '')
        """,
        (session_id,),
    )


async def _insert_agent(db, session_id: str, agent_id: int, username: str) -> None:
    await db.execute(
        """
        INSERT INTO agent_profiles
            (id, session_id, agent_type, age, sex, district, occupation,
             income_bracket, education_level, marital_status, housing_type,
             openness, conscientiousness, extraversion, agreeableness,
             neuroticism, monthly_income, savings, oasis_persona, oasis_username)
        VALUES (?, ?, 'customer', 30, 'F', 'Central', 'Analyst',
                'middle', 'degree', 'single', 'rent',
                0.5, 0.5, 0.5, 0.5, 0.5, 30000, 100000, 'Test persona', ?)
        """,
        (agent_id, session_id, username),
    )


@pytest.mark.asyncio
async def test_process_round_creates_memory_triples_and_belief_edges(test_db):
    session_id = "sess_stage6"
    await _insert_session(test_db, session_id)
    await _insert_agent(test_db, session_id, 1, "alice")
    await test_db.execute(
        """
        INSERT INTO simulation_actions
            (session_id, round_number, agent_id, oasis_username, action_type,
             platform, content, sentiment, topics)
        VALUES (?, 1, 1, 'alice', 'post', 'reddit',
                '我支持新產品，優惠影響銷量。', 'positive', '["新產品"]')
        """,
        (session_id,),
    )
    await test_db.commit()

    @asynccontextmanager
    async def _mock_get_db():
        yield test_db

    with patch("backend.app.services.simulation_memory_graph_loop.get_db", _mock_get_db):
        stats = await SimulationMemoryGraphLoop().process_round(session_id, 1)

    assert stats.actions_seen == 1
    assert stats.memories_added == 1
    assert stats.triples_added >= 1
    assert stats.kg_nodes_added >= 2
    assert stats.kg_edges_added >= 1

    memory = await (
        await test_db.execute(
            "SELECT memory_text, metadata FROM agent_memories WHERE session_id = ?",
            (session_id,),
        )
    ).fetchone()
    assert memory is not None
    assert "新產品" in memory["memory_text"]
    assert '"source": "simulation_action"' in memory["metadata"]

    edge = await (
        await test_db.execute(
            """
            SELECT relation_type, layer_type, source_agent_id, round_number
            FROM kg_edges
            WHERE session_id = ? AND layer_type = 'belief'
            LIMIT 1
            """,
            (session_id,),
        )
    ).fetchone()
    assert edge is not None
    assert edge["relation_type"].startswith("BELIEVES_")
    assert edge["source_agent_id"] == "1"
    assert edge["round_number"] == 1


@pytest.mark.asyncio
async def test_process_round_is_idempotent_per_action(test_db):
    session_id = "sess_stage6_idempotent"
    await _insert_session(test_db, session_id)
    await _insert_agent(test_db, session_id, 1, "alice")
    await test_db.execute(
        """
        INSERT INTO simulation_actions
            (session_id, round_number, agent_id, oasis_username, action_type,
             platform, content, sentiment, topics)
        VALUES (?, 2, 1, 'alice', 'post', 'twitter',
                '我反對加價，價格上升會影響需求。', 'negative', '["價格"]')
        """,
        (session_id,),
    )
    await test_db.commit()

    @asynccontextmanager
    async def _mock_get_db():
        yield test_db

    with patch("backend.app.services.simulation_memory_graph_loop.get_db", _mock_get_db):
        first = await SimulationMemoryGraphLoop().process_round(session_id, 2)
        second = await SimulationMemoryGraphLoop().process_round(session_id, 2)

    assert first.memories_added == 1
    assert second.memories_added == 0

    count = await (
        await test_db.execute(
            "SELECT COUNT(*) AS count FROM agent_memories WHERE session_id = ?",
            (session_id,),
        )
    ).fetchone()
    assert count["count"] == 1


@pytest.mark.asyncio
async def test_process_round_resolves_missing_action_agent_id_from_username(test_db):
    session_id = "sess_stage6_resolve"
    await _insert_session(test_db, session_id)
    await _insert_agent(test_db, session_id, 7, "bob")
    await test_db.execute(
        """
        INSERT INTO simulation_actions
            (session_id, round_number, agent_id, oasis_username, action_type,
             platform, content, sentiment, topics)
        VALUES (?, 1, NULL, 'bob', 'create_comment', 'reddit',
                '我見到競爭對手降價。', 'neutral', '["競爭"]')
        """,
        (session_id,),
    )
    await test_db.commit()

    @asynccontextmanager
    async def _mock_get_db():
        yield test_db

    with patch("backend.app.services.simulation_memory_graph_loop.get_db", _mock_get_db):
        stats = await SimulationMemoryGraphLoop().process_round(session_id, 1)

    assert stats.memories_added == 1
    memory = await (
        await test_db.execute(
            "SELECT agent_id FROM agent_memories WHERE session_id = ?",
            (session_id,),
        )
    ).fetchone()
    assert memory["agent_id"] == 7

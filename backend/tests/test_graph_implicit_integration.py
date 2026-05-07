# backend/tests/test_graph_implicit_integration.py
"""Tests for the canonical graph-build API path."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_build_graph_uses_canonical_builder(test_client):
    """build_graph should delegate to the canonical GraphBuilderService path."""
    mock_result = {
        "graph_id": "graph-123",
        "session_id": "graph-123",
        "node_count": 4,
        "edge_count": 3,
        "entity_types": ["Person"],
        "relation_types": ["RELATED_TO"],
        "seed_nodes": 2,
        "seed_edges": 1,
        "implicit_nodes": 2,
        "world_context_count": 0,
        "persona_template_count": 0,
    }

    with patch(
        "backend.app.api.graph.GraphBuilderService.build_graph_from_seed",
        new=AsyncMock(return_value=mock_result),
    ) as build_graph_from_seed:
        resp = await test_client.post(
            "/api/graph/build",
            json={
                "scenario_type": "macro",
                "seed_text": "US-Iran war began Feb 28 2026",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["graph_id"] == "graph-123"
    assert data["data"]["session_id"] == "graph-123"
    assert data["meta"]["implicit_nodes"] == 2
    build_graph_from_seed.assert_awaited_once()

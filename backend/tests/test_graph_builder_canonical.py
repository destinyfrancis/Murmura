from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.services.graph_builder import GraphBuilderService
from backend.app.services.implicit_stakeholder_service import DiscoveryResult
from backend.app.services.scenario_intake import ScenarioIntakeService
from backend.app.services.text_processor import ProcessedSeed, SeedEntity, Stakeholder


@pytest.mark.asyncio
async def test_canonical_graph_build_creates_holder_and_evidence(test_client) -> None:
    """Real /graph/build path should satisfy FK constraints and attach evidence."""
    processed = ProcessedSeed(
        language="en",
        entities=(
            SeedEntity(name="Alice", type="person", relevance=0.9),
            SeedEntity(name="Bob", type="person", relevance=0.8),
        ),
        timeline=(),
        stakeholders=(Stakeholder(group="Customers", impact="high", description="Customers affected by Alice"),),
        sentiment="mixed",
        key_claims=("Alice challenges Bob in the launch market.",),
        suggested_scenario="market",
        suggested_regions=(),
        confidence=0.9,
    )

    mock_processor = AsyncMock()
    mock_processor.process = AsyncMock(return_value=processed)
    mock_mem = AsyncMock()
    mock_mem.build_from_graph = AsyncMock(
        return_value=SimpleNamespace(world_context_count=0, persona_template_count=0, enhanced_edge_count=0)
    )

    with (
        patch("backend.app.services.text_processor.TextProcessor", return_value=mock_processor),
        patch(
            "backend.app.services.implicit_stakeholder_service.ImplicitStakeholderService.discover",
            new=AsyncMock(return_value=DiscoveryResult(stakeholders=(), nodes_added=0)),
        ),
        patch("backend.app.services.memory_initialization.MemoryInitializationService", return_value=mock_mem),
    ):
        response = await test_client.post(
            "/api/graph/build",
            json={
                "scenario_type": "b2b",
                "seed_text": "Alice challenges Bob in the launch market. Customers react quickly.",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    graph_id = payload["data"]["graph_id"]
    assert payload["data"]["node_count"] >= 2
    assert payload["data"]["edge_count"] >= 1
    assert payload["meta"]["chunk_count"] == 1

    graph_response = await test_client.get(f"/api/graph/{graph_id}")
    graph_payload = graph_response.json()["data"]
    assert graph_payload["edges"][0]["source_text"]
    assert graph_payload["edges"][0]["evidence_span"]


@pytest.mark.asyncio
async def test_graph_build_fallback_preserves_long_seed(test_client) -> None:
    """Empty extraction should still return a fallback KG for long seeds."""
    long_seed = "香港樓市加息，銀行收緊按揭，業主同租客重新判斷風險。" * 180
    processed = ProcessedSeed(
        language="zh",
        entities=(),
        timeline=(),
        stakeholders=(),
        sentiment="mixed",
        key_claims=(),
        suggested_scenario="property",
        suggested_regions=(),
        confidence=0.1,
    )

    mock_processor = AsyncMock()
    mock_processor.process = AsyncMock(return_value=processed)
    mock_mem = AsyncMock()
    mock_mem.build_from_graph = AsyncMock(
        return_value=SimpleNamespace(world_context_count=0, persona_template_count=0, enhanced_edge_count=0)
    )

    with (
        patch("backend.app.services.text_processor.TextProcessor", return_value=mock_processor),
        patch(
            "backend.app.services.implicit_stakeholder_service.ImplicitStakeholderService.discover",
            new=AsyncMock(return_value=DiscoveryResult(stakeholders=(), nodes_added=0)),
        ),
        patch("backend.app.services.memory_initialization.MemoryInitializationService", return_value=mock_mem),
    ):
        response = await test_client.post(
            "/api/graph/build",
            json={"scenario_type": "property", "seed_text": long_seed},
        )

    assert response.status_code == 200
    payload = response.json()
    graph_id = payload["data"]["graph_id"]
    assert payload["data"]["node_count"] >= 3
    assert payload["data"]["edge_count"] >= 2

    graph_response = await test_client.get(f"/api/graph/{graph_id}")
    graph_payload = graph_response.json()["data"]
    assert graph_payload["nodes"]
    assert graph_payload["edges"]


def test_edge_evidence_prefers_chunk_with_both_endpoints() -> None:
    service = GraphBuilderService()
    intake = ScenarioIntakeService(chunk_chars=55, chunk_overlap=0).from_text(
        "Alpha mentioned an unrelated supplier risk.\n\n"
        "Later, Alice signs a distribution deal with Bob in Singapore.",
        source_ref="market.md",
    )

    evidence = service._find_edge_evidence(
        source_title="Alice",
        target_title="Bob",
        description="distribution deal",
        relation_type="DISTRIBUTES",
        chunks=intake.chunks,
    )

    assert evidence is not None
    assert "Alice" in evidence["text"]
    assert "Bob" in evidence["text"]
    assert evidence["chunk_index"] == 1

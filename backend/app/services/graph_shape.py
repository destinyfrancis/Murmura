"""Graph-shape comparison helpers for ingestion stability checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GraphShape:
    """Compact, deterministic summary of a knowledge graph extraction."""

    node_count: int
    edge_count: int
    entity_type_counts: dict[str, int]
    relation_type_counts: dict[str, int]


@dataclass(frozen=True)
class GraphShapeComparison:
    """Tolerance result for two graph shapes."""

    within_tolerance: bool
    node_delta_ratio: float
    edge_delta_ratio: float
    missing_entity_types: tuple[str, ...]
    missing_relation_types: tuple[str, ...]


def graph_shape_from_extraction(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> GraphShape:
    """Create a stable graph-shape summary from extracted nodes and edges."""
    entity_counts: dict[str, int] = {}
    relation_counts: dict[str, int] = {}

    for node in nodes:
        entity_type = str(node.get("entity_type") or "Unknown")
        entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

    for edge in edges:
        relation_type = str(edge.get("relation_type") or "UNKNOWN")
        relation_counts[relation_type] = relation_counts.get(relation_type, 0) + 1

    return GraphShape(
        node_count=len(nodes),
        edge_count=len(edges),
        entity_type_counts=dict(sorted(entity_counts.items())),
        relation_type_counts=dict(sorted(relation_counts.items())),
    )


def compare_graph_shapes(
    baseline: GraphShape,
    candidate: GraphShape,
    *,
    count_tolerance_ratio: float = 0.15,
) -> GraphShapeComparison:
    """Compare two extraction shapes with count tolerance and type coverage."""
    node_delta_ratio = _delta_ratio(baseline.node_count, candidate.node_count)
    edge_delta_ratio = _delta_ratio(baseline.edge_count, candidate.edge_count)
    missing_entity_types = tuple(sorted(set(baseline.entity_type_counts) - set(candidate.entity_type_counts)))
    missing_relation_types = tuple(sorted(set(baseline.relation_type_counts) - set(candidate.relation_type_counts)))

    return GraphShapeComparison(
        within_tolerance=(
            node_delta_ratio <= count_tolerance_ratio
            and edge_delta_ratio <= count_tolerance_ratio
            and not missing_entity_types
            and not missing_relation_types
        ),
        node_delta_ratio=node_delta_ratio,
        edge_delta_ratio=edge_delta_ratio,
        missing_entity_types=missing_entity_types,
        missing_relation_types=missing_relation_types,
    )


def _delta_ratio(baseline: int, candidate: int) -> float:
    if baseline == candidate:
        return 0.0
    denominator = max(1, baseline)
    return abs(candidate - baseline) / denominator

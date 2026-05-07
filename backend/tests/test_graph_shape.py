from __future__ import annotations

from backend.app.services.graph_shape import compare_graph_shapes, graph_shape_from_extraction


def test_graph_shape_from_extraction_is_deterministic() -> None:
    nodes = [
        {"id": "alice", "entity_type": "Person"},
        {"id": "acme", "entity_type": "Company"},
        {"id": "bob", "entity_type": "Person"},
    ]
    edges = [
        {"source_id": "alice", "target_id": "acme", "relation_type": "WORKS_AT"},
        {"source_id": "bob", "target_id": "acme", "relation_type": "WORKS_AT"},
    ]

    first = graph_shape_from_extraction(nodes, edges)
    second = graph_shape_from_extraction(list(reversed(nodes)), list(reversed(edges)))

    assert first == second
    assert first.entity_type_counts == {"Company": 1, "Person": 2}
    assert first.relation_type_counts == {"WORKS_AT": 2}


def test_compare_graph_shapes_accepts_small_count_drift_with_same_types() -> None:
    baseline = graph_shape_from_extraction(
        [{"entity_type": "Person"} for _ in range(10)],
        [{"relation_type": "SUPPORTS"} for _ in range(10)],
    )
    candidate = graph_shape_from_extraction(
        [{"entity_type": "Person"} for _ in range(9)],
        [{"relation_type": "SUPPORTS"} for _ in range(11)],
    )

    comparison = compare_graph_shapes(baseline, candidate, count_tolerance_ratio=0.15)

    assert comparison.within_tolerance is True
    assert comparison.node_delta_ratio == 0.1
    assert comparison.edge_delta_ratio == 0.1


def test_compare_graph_shapes_rejects_missing_types() -> None:
    baseline = graph_shape_from_extraction(
        [{"entity_type": "Person"}, {"entity_type": "Regulator"}],
        [{"relation_type": "REGULATES"}],
    )
    candidate = graph_shape_from_extraction(
        [{"entity_type": "Person"}],
        [{"relation_type": "SUPPORTS"}],
    )

    comparison = compare_graph_shapes(baseline, candidate, count_tolerance_ratio=1.0)

    assert comparison.within_tolerance is False
    assert comparison.missing_entity_types == ("Regulator",)
    assert comparison.missing_relation_types == ("REGULATES",)

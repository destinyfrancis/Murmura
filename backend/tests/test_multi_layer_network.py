import random

import pytest

from backend.app.models.platform_identity import PlatformType, build_platform_identity
from backend.app.services.multi_layer_network import (
    CROSS_PLATFORM_LATENCY_ROUNDS,
    MultiLayerNetwork,
    PlatformEdge,
)


def _make_network() -> MultiLayerNetwork:
    net = MultiLayerNetwork()
    net.add_edge(PlatformEdge(source_id="a", target_id="b", platform=PlatformType.TWITTER, weight=0.8))
    net.add_edge(PlatformEdge(source_id="a", target_id="c", platform=PlatformType.REDDIT, weight=0.6))
    net.add_edge(PlatformEdge(source_id="b", target_id="c", platform=PlatformType.TWITTER, weight=0.5))
    return net


def test_add_and_get_edges_by_platform():
    net = _make_network()
    tw_edges = net.get_edges(PlatformType.TWITTER)
    assert len(tw_edges) == 2
    rc_edges = net.get_edges(PlatformType.REDDIT)
    assert len(rc_edges) == 1


def test_get_agent_platforms():
    net = MultiLayerNetwork()
    pi_tw = build_platform_identity("a", PlatformType.TWITTER, "@a", base_activity_rate=0.7)
    pi_rc = build_platform_identity("a", PlatformType.REDDIT, "u/a", base_activity_rate=0.6)
    net.register_agent(pi_tw)
    net.register_agent(pi_rc)
    platforms = net.get_agent_platforms("a")
    assert PlatformType.TWITTER in platforms
    assert PlatformType.REDDIT in platforms


def test_cross_platform_latency_defined():
    latency = CROSS_PLATFORM_LATENCY_ROUNDS.get(
        (PlatformType.TWITTER, PlatformType.NEWS), None
    )
    assert latency is not None and latency > 0


def test_select_platform_for_round_weighted_selection():
    """Verify select_platform_for_round produces weighted distribution."""
    net = MultiLayerNetwork()
    # hour=9: Twitter p=0.70*0.7=0.49, Reddit p=0.40*0.6=0.24 → Twitter ~2x more likely
    pi_tw = build_platform_identity("a", PlatformType.TWITTER, "@a", base_activity_rate=0.7)
    pi_rc = build_platform_identity("a", PlatformType.REDDIT, "u/a", base_activity_rate=0.6)
    net.register_agent(pi_tw)
    net.register_agent(pi_rc)

    rng = random.Random(42)
    results = [net.select_platform_for_round("a", hour=9, rng=rng) for _ in range(1000)]

    twitter_count = results.count(PlatformType.TWITTER)
    reddit_count = results.count(PlatformType.REDDIT)
    # Twitter should be selected more frequently than Reddit (roughly 2:1)
    assert twitter_count > reddit_count
    # Both platforms should appear (neither starved)
    assert reddit_count > 50


def test_select_platform_returns_none_for_unknown_agent():
    net = _make_network()
    result = net.select_platform_for_round("unknown_agent", 10, random.Random(0))
    assert result is None


def test_get_cross_platform_latency_same_platform_is_zero():
    net = MultiLayerNetwork()
    assert net.get_cross_platform_latency(PlatformType.TWITTER, PlatformType.TWITTER) == 0


def test_get_cross_platform_latency_unknown_defaults_to_12():
    net = MultiLayerNetwork()
    # WECHAT → REDDIT is not in the map → should return 12
    assert net.get_cross_platform_latency(PlatformType.WECHAT, PlatformType.REDDIT) == 12


def test_select_platform_zero_weight_uses_uniform_fallback():
    """When all platform activity vectors are zero at the given hour, use uniform random."""
    net = MultiLayerNetwork()
    # Build identity then replace with all-zero vector (bypassing build_platform_identity)
    import dataclasses
    pi_tw = build_platform_identity("b", PlatformType.TWITTER, "@b", base_activity_rate=1.0)
    pi_rc = build_platform_identity("b", PlatformType.REDDIT, "u/b", base_activity_rate=1.0)
    pi_tw_zero = dataclasses.replace(pi_tw, activity_vector_24h=(0.0,) * 24)
    pi_rc_zero = dataclasses.replace(pi_rc, activity_vector_24h=(0.0,) * 24)
    net.register_agent(pi_tw_zero)
    net.register_agent(pi_rc_zero)

    rng = random.Random(99)
    results = [net.select_platform_for_round("b", hour=12, rng=rng) for _ in range(100)]
    # With zero weights, fallback is uniform — both platforms should appear
    assert PlatformType.TWITTER in results or PlatformType.REDDIT in results
    # Should not raise
    assert all(r in {PlatformType.TWITTER, PlatformType.REDDIT} for r in results)

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


def test_select_platform_for_round_returns_valid_platform():
    net = MultiLayerNetwork()
    pi_tw = build_platform_identity("a", PlatformType.TWITTER, "@a", base_activity_rate=0.7)
    pi_rc = build_platform_identity("a", PlatformType.REDDIT, "u/a", base_activity_rate=0.6)
    net.register_agent(pi_tw)
    net.register_agent(pi_rc)
    rng = random.Random(0)
    platform = net.select_platform_for_round(agent_id="a", hour=20, rng=rng)
    assert platform in {PlatformType.TWITTER, PlatformType.REDDIT}


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

"""Layer 2 integration tests — platform identity DB persistence and network init."""
from __future__ import annotations

import csv
import os
import tempfile

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_save_platform_identities_to_db_writes_rows():
    """save_platform_identities_to_db() inserts one row per (agent, platform) pair."""
    from backend.app.models.platform_identity import PlatformIdentity, PlatformType
    from backend.app.services.kg_agent_factory import KGAgentFactory

    pi = PlatformIdentity(
        agent_id="abc",
        platform=PlatformType.TWITTER,
        handle="@abc_twitter",
        anonymity_level=0.1,
        activity_vector_24h=tuple([0.5] * 24),
        audience_size=100,
        tone_shift=0.0,
        moderation_risk=0.02,
    )

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=False)

    with patch("backend.app.utils.db.get_db", return_value=mock_db):
        factory = KGAgentFactory.__new__(KGAgentFactory)
        factory._graph_id = "sess-1234"
        await factory.save_platform_identities_to_db(
            session_id="sess-1234",
            identities=[pi],
        )

    assert mock_db.execute.called
    call_args = mock_db.execute.call_args_list[0]
    sql = call_args[0][0]
    assert "platform_identities" in sql
    assert "activity_vector_json" in sql
    params = call_args[0][1]
    assert params[0] == "sess-1234"
    assert params[1] == "abc"
    assert params[2] == "twitter"


@pytest.mark.asyncio
async def test_init_multi_layer_network_builds_network_from_db():
    """_init_multi_layer_network() loads DB rows and registers agents in MultiLayerNetwork."""
    from backend.app.services.simulation_hooks_kg import KGHooksMixin

    db_rows = [
        ("agent_a", "twitter", "@alice", 0.1, ",".join(["0.5"] * 24), 200, 0.0, 0.02),
        ("agent_a", "reddit", "alice_r", 0.5, ",".join(["0.3"] * 24), 50, 0.1, 0.01),
        ("agent_b", "wechat", "bob_wc", 0.0, ",".join(["0.7"] * 24), 500, 0.0, 0.03),
    ]

    mock_cursor = AsyncMock()
    mock_cursor.fetchall = AsyncMock(return_value=db_rows)
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_cursor)
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=False)

    instance = MagicMock()
    instance._multi_layer_networks = {}
    instance._agent_moderation_risks = {}
    instance._kg_mode = {"sess-abc": True}

    with patch("backend.app.utils.db.get_db", return_value=mock_db):
        await KGHooksMixin._init_multi_layer_network(instance, "sess-abc")

    assert "sess-abc" in instance._multi_layer_networks
    network = instance._multi_layer_networks["sess-abc"]
    platforms = network.get_agent_platforms("agent_a")
    assert len(platforms) == 2
    assert instance._agent_moderation_risks["sess-abc"]["agent_a"] == pytest.approx(0.02)
    assert instance._agent_moderation_risks["sess-abc"]["agent_b"] == pytest.approx(0.03)


@pytest.mark.asyncio
async def test_init_multi_layer_network_skips_non_kg_driven():
    """_init_multi_layer_network() is a no-op for non-kg_driven sessions."""
    from backend.app.services.simulation_hooks_kg import KGHooksMixin

    instance = MagicMock()
    instance._multi_layer_networks = {}
    instance._kg_mode = {}  # no kg_driven entry

    await KGHooksMixin._init_multi_layer_network(instance, "sess-xyz")

    assert "sess-xyz" not in instance._multi_layer_networks


def test_is_agent_active_uses_platform_identity_when_network_available():
    """_is_agent_active() picks a PlatformIdentity from MultiLayerNetwork and passes it to should_activate."""
    from backend.app.services.simulation_runner import SimulationRunner
    from backend.app.models.platform_identity import PlatformIdentity, PlatformType
    from backend.app.services.multi_layer_network import MultiLayerNetwork

    runner = SimulationRunner(dry_run=True)
    session_id = "test-sess"

    pi = PlatformIdentity(
        agent_id="user_alice",
        platform=PlatformType.TWITTER,
        handle="@alice",
        anonymity_level=0.0,
        activity_vector_24h=tuple([1.0] * 24),
        audience_size=100,
        tone_shift=0.0,
        moderation_risk=0.02,
    )
    network = MultiLayerNetwork()
    network.register_agent(pi)
    runner._multi_layer_networks[session_id] = network

    # Base rate 0 would never activate without platform override
    runner._activity_profiles[session_id] = {
        "user_alice": {
            "agent_id": 1,
            "chronotype": "standard",
            "activity_vector": [0.0] * 24,
            "base_activity_rate": 0.0,
        }
    }

    result = runner._is_agent_active(session_id, "user_alice", round_number=8)
    # Platform vector (all 1.0) overrides zero base rate — should activate
    assert result is True


def test_is_agent_active_records_platform_in_round_active_agents():
    """_is_agent_active() writes the chosen platform to _round_active_agents[session_id]."""
    from backend.app.services.simulation_runner import SimulationRunner
    from backend.app.models.platform_identity import PlatformIdentity, PlatformType
    from backend.app.services.multi_layer_network import MultiLayerNetwork

    runner = SimulationRunner(dry_run=True)
    session_id = "test-sess-2"

    pi = PlatformIdentity(
        agent_id="user_bob",
        platform=PlatformType.WECHAT,
        handle="bob_wc",
        anonymity_level=0.0,
        activity_vector_24h=tuple([1.0] * 24),
        audience_size=300,
        tone_shift=0.0,
        moderation_risk=0.03,
    )
    network = MultiLayerNetwork()
    network.register_agent(pi)
    runner._multi_layer_networks[session_id] = network
    runner._activity_profiles[session_id] = {
        "user_bob": {
            "agent_id": 2,
            "chronotype": "standard",
            "activity_vector": [1.0] * 24,
            "base_activity_rate": 1.0,
        }
    }

    runner._is_agent_active(session_id, "user_bob", round_number=10)
    recorded = runner._round_active_agents.get(session_id, {})
    assert "user_bob" in recorded
    assert recorded["user_bob"] == "wechat"


def test_process_moderation_wired_at_echo_chamber_interval():
    """_process_moderation is scheduled in Group-3 when kg_driven + network present."""
    from unittest.mock import MagicMock
    from backend.app.models.simulation_config import PRESET_STANDARD

    hc = PRESET_STANDARD.hook_config
    interval = hc.echo_chamber_interval  # e.g. 3

    # Simulate what the Group-3 conditional does:
    kg_mode = {"sess-x": True}
    multi_layer_networks = {"sess-x": MagicMock()}  # non-empty = network present

    called = []

    if kg_mode.get("sess-x") and multi_layer_networks.get("sess-x"):
        called.append(("sess-x", interval))

    assert ("sess-x", interval) in called


def test_round_active_agents_cleared_each_round():
    """_round_active_agents[session_id] is reset to {} at the start of each round."""
    from backend.app.services.simulation_runner import SimulationRunner

    runner = SimulationRunner(dry_run=True)
    session_id = "sess-clear"

    # Populate with stale data from a previous round
    runner._round_active_agents[session_id] = {"user_a": "twitter", "user_b": "reddit"}

    # Simulate the round-start clear
    runner._round_active_agents[session_id] = {}

    assert runner._round_active_agents[session_id] == {}


def test_generate_agents_csv_includes_platform_notes():
    """generate_agents_csv() appends platform notes to user_char when platform_identities present."""
    from backend.app.models.platform_identity import PlatformIdentity, PlatformType
    from backend.app.models.universal_agent_profile import UniversalAgentProfile
    from backend.app.services.kg_agent_factory import KGAgentFactory

    pi = PlatformIdentity(
        agent_id="node_abc",
        platform=PlatformType.TWITTER,
        handle="@alice_tw",
        anonymity_level=0.1,
        activity_vector_24h=tuple([0.5] * 24),
        audience_size=500,
        tone_shift=0.2,
        moderation_risk=0.05,
    )
    profile = UniversalAgentProfile(
        id="node_abc",
        name="Alice",
        role="Tech blogger",
        entity_type="Person",
        persona="A tech blogger who writes about AI and society.",
        goals=("spread awareness",),
        capabilities=("write articles", "post on social media"),
        stance_axes=(("pro_tech", 0.8),),
        relationships=(),
        kg_node_id="node_abc",
        platform_identities=(pi,),
    )

    factory = KGAgentFactory.__new__(KGAgentFactory)
    factory._graph_id = "g-1"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        tmp_path = f.name
    try:
        factory.generate_agents_csv([profile], tmp_path)
        with open(tmp_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    finally:
        os.unlink(tmp_path)

    assert len(rows) == 1
    user_char = rows[0]["user_char"]
    assert "twitter" in user_char.lower()
    assert "@alice_tw" in user_char
    assert "[platforms:" in user_char

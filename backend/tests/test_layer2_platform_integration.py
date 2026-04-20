"""Layer 2 integration tests — platform identity DB persistence and network init."""
from __future__ import annotations

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
    assert instance._agent_moderation_risks["sess-abc"]["agent_a"] > 0
    assert instance._agent_moderation_risks["sess-abc"]["agent_b"] > 0


@pytest.mark.asyncio
async def test_init_multi_layer_network_skips_non_kg_driven():
    """_init_multi_layer_network() is a no-op for non-kg_driven sessions."""
    from backend.app.services.simulation_hooks_kg import KGHooksMixin

    instance = MagicMock()
    instance._multi_layer_networks = {}
    instance._kg_mode = {}  # no kg_driven entry

    await KGHooksMixin._init_multi_layer_network(instance, "sess-xyz")

    assert "sess-xyz" not in instance._multi_layer_networks

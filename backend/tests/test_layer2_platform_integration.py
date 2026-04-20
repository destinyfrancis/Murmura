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

    with patch("backend.app.services.kg_agent_factory.get_db", return_value=mock_db):
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
    params = call_args[0][1]
    assert params[0] == "sess-1234"
    assert params[1] == "abc"
    assert params[2] == "twitter"

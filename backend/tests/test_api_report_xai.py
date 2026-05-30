"""Unit tests for the POST /report/{session_id}/xai-tool endpoint."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.app.utils.db import get_db


async def _auth_headers_for_session(test_client, session_id: str) -> dict[str, str]:
    resp = await test_client.post(
        "/api/auth/register",
        json={"email": f"xai-{session_id}@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    async with get_db() as db:
        await db.execute(
            """INSERT INTO simulation_sessions
               (id, name, sim_mode, agent_count, round_count, llm_provider, owner_id)
               VALUES (?, ?, 'kg_driven', 1, 1, 'test', ?)""",
            (session_id, session_id, data["user_id"]),
        )
        await db.commit()
    return {"Authorization": f"Bearer {data['token']}"}


@pytest.mark.asyncio
async def test_invoke_xai_tool_unknown_returns_400(test_client):
    """Requesting a tool name that is not in TOOLS must return HTTP 400."""
    headers = await _auth_headers_for_session(test_client, "test-session")
    resp = await test_client.post(
        "/api/report/test-session/xai-tool",
        json={"tool_name": "not_a_real_tool"},
        headers=headers,
    )
    assert resp.status_code == 400
    body = resp.json()
    assert "Unknown tool" in body.get("detail", "")


@pytest.mark.asyncio
async def test_invoke_xai_tool_calls_handler(test_client):
    """A valid tool name must invoke its handler and return the result."""
    headers = await _auth_headers_for_session(test_client, "test-session")
    mock_handler = AsyncMock(return_value={"gdp": 3.1})
    fake_tools = {"get_macro_context": "Get macro context"}
    fake_handlers = {"get_macro_context": mock_handler}

    with (
        patch("backend.app.services.report_agent.TOOLS", fake_tools),
        patch("backend.app.services.report_agent._TOOL_HANDLERS", fake_handlers),
    ):
        resp = await test_client.post(
            "/api/report/test-session/xai-tool",
            json={"tool_name": "get_macro_context"},
            headers=headers,
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["tool"] == "get_macro_context"
    assert body["data"]["result"]["gdp"] == 3.1
    mock_handler.assert_called_once_with("test-session")


@pytest.mark.asyncio
async def test_invoke_xai_tool_no_handler_returns_501(test_client):
    """If a tool exists in TOOLS but has no handler entry, return HTTP 501."""
    headers = await _auth_headers_for_session(test_client, "test-session")
    fake_tools = {"orphan_tool": "A tool without a handler"}
    fake_handlers: dict = {}  # no handler registered

    with (
        patch("backend.app.services.report_agent.TOOLS", fake_tools),
        patch("backend.app.services.report_agent._TOOL_HANDLERS", fake_handlers),
    ):
        resp = await test_client.post(
            "/api/report/test-session/xai-tool",
            json={"tool_name": "orphan_tool"},
            headers=headers,
        )

    assert resp.status_code == 501


@pytest.mark.asyncio
async def test_invoke_xai_tool_handler_exception_returns_success_false(test_client):
    """If the handler raises an unexpected exception the endpoint returns success=False."""
    headers = await _auth_headers_for_session(test_client, "test-session")
    failing_handler = AsyncMock(side_effect=RuntimeError("db unavailable"))
    fake_tools = {"get_macro_context": "Get macro context"}
    fake_handlers = {"get_macro_context": failing_handler}

    with (
        patch("backend.app.services.report_agent.TOOLS", fake_tools),
        patch("backend.app.services.report_agent._TOOL_HANDLERS", fake_handlers),
    ):
        resp = await test_client.post(
            "/api/report/test-session/xai-tool",
            json={"tool_name": "get_macro_context"},
            headers=headers,
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    # Error message must NOT leak internal exception details (T13 security fix).
    # Production returns generic "Internal server error"; details logged server-side.
    assert body.get("error") == "Internal server error"


@pytest.mark.asyncio
async def test_invoke_xai_tool_passes_extra_params(test_client):
    """Extra params in the request body must be forwarded as kwargs to the handler."""
    headers = await _auth_headers_for_session(test_client, "sess-abc")
    mock_handler = AsyncMock(return_value={"hits": 5})
    fake_tools = {"query_graph": "Semantic KG query"}
    fake_handlers = {"query_graph": mock_handler}

    with (
        patch("backend.app.services.report_agent.TOOLS", fake_tools),
        patch("backend.app.services.report_agent._TOOL_HANDLERS", fake_handlers),
    ):
        resp = await test_client.post(
            "/api/report/sess-abc/xai-tool",
            json={"tool_name": "query_graph", "params": {"topic": "housing"}},
            headers=headers,
        )

    assert resp.status_code == 200
    mock_handler.assert_called_once_with("sess-abc", topic="housing")

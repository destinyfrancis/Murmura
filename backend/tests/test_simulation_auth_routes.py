from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_resume_requires_authentication(test_client) -> None:
    response = await test_client.post("/api/simulation/session-auth-smoke/resume")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_live_shock_requires_authentication(test_client) -> None:
    response = await test_client.post(
        "/api/simulation/session-auth-smoke/shock",
        json={
            "round_number": 1,
            "shock_type": "policy",
            "description": "Smoke shock",
            "post_content": "Smoke shock",
            "parameters": {},
        },
    )

    assert response.status_code == 401

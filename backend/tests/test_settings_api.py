from __future__ import annotations

import httpx
import pytest

from backend.app.api.auth import UserProfile
from backend.app.utils.db import get_db
from backend.app.services import runtime_settings

_TEST_ADMIN = UserProfile(id="admin", email="admin@example.com", is_admin=True)
_TEST_KEY = "sk-or-secret-settings-key"


@pytest.fixture(autouse=True)
def clear_runtime_settings() -> None:
    runtime_settings._store.clear()
    yield
    runtime_settings._store.clear()


@pytest.mark.asyncio
async def test_update_settings_accepts_canonical_step_runtime_keys(monkeypatch) -> None:
    """PUT /settings should accept both frontend fields and RuntimeSettings keys."""
    from backend.app.api import settings as settings_api

    persisted: list[tuple[str, str]] = []

    async def fake_persist_to_db(key: str, value: str) -> None:
        persisted.append((key, value))

    monkeypatch.setattr(settings_api, "_persist_to_db", fake_persist_to_db)

    req = settings_api.SettingsUpdateRequest(
        **{
            "step1_llm_provider": "openrouter",
            "step1_llm_model": "deepseek/deepseek-chat-v3.1",
            "step3_llm_model_lite": "openrouter/cheap-model",
        }
    )
    result = await settings_api.update_settings(req, _user=_TEST_ADMIN)

    assert result["success"] is True
    assert runtime_settings.get_override("step1_llm_provider") == "openrouter"
    assert runtime_settings.get_override("step1_llm_model") == "deepseek/deepseek-chat-v3.1"
    assert runtime_settings.get_override("step3_llm_model_lite") == "openrouter/cheap-model"
    assert ("step1_llm_provider", "openrouter") in persisted


@pytest.mark.asyncio
async def test_update_settings_short_step_fields_still_route_to_runtime_keys(monkeypatch) -> None:
    from backend.app.api import settings as settings_api

    async def fake_persist_to_db(key: str, value: str) -> None:
        return None

    monkeypatch.setattr(settings_api, "_persist_to_db", fake_persist_to_db)

    req = settings_api.SettingsUpdateRequest(step4_provider="openrouter", step4_model="report-model")
    await settings_api.update_settings(req, _user=_TEST_ADMIN)

    assert runtime_settings.get_override("step4_llm_provider") == "openrouter"
    assert runtime_settings.get_override("step4_llm_model") == "report-model"


@pytest.mark.asyncio
async def test_openrouter_key_validation_uses_current_key_endpoint(monkeypatch) -> None:
    from backend.app.api import settings as settings_api

    calls: list[str] = []

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args) -> None:
            return None

        async def get(self, url: str, headers: dict[str, str]) -> httpx.Response:
            calls.append(url)
            return httpx.Response(200, json={"data": {"label": "test-key"}})

    monkeypatch.setattr(settings_api.httpx, "AsyncClient", FakeAsyncClient)

    result = await settings_api._test_provider_key("openrouter", "sk-or-test")

    assert result["ok"] is True
    assert calls == ["https://openrouter.ai/api/v1/key"]


@pytest.mark.asyncio
async def test_openrouter_model_validation_posts_chat_completion(monkeypatch) -> None:
    from backend.app.api import settings as settings_api

    calls: list[tuple[str, dict[str, object]]] = []

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args) -> None:
            return None

        async def post(self, url: str, **kwargs) -> httpx.Response:
            calls.append((url, kwargs))
            return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr(settings_api.httpx, "AsyncClient", FakeAsyncClient)

    result = await settings_api._test_provider_model("openrouter", "sk-or-test", "openai/gpt-4o-mini")

    assert result["ok"] is True
    assert calls[0][0] == "https://openrouter.ai/api/v1/chat/completions"
    assert calls[0][1]["json"]["model"] == "openai/gpt-4o-mini"


async def _register_user(client, email: str, *, is_admin: bool = False) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    if is_admin:
        async with get_db() as db:
            await db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (body["user_id"],))
            await db.commit()
    return body["token"]


@pytest.mark.asyncio
async def test_settings_endpoints_reject_anonymous(test_client) -> None:
    requests = [
        ("GET", "/api/settings", None),
        ("PUT", "/api/settings", {"agent_provider": "openrouter"}),
        ("POST", "/api/settings/test-key", {"provider": "openrouter", "api_key": _TEST_KEY}),
        ("POST", "/api/settings/models", {"provider": "openrouter", "api_key": _TEST_KEY}),
    ]

    for method, url, json_body in requests:
        resp = await test_client.request(method, url, json=json_body)
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_settings_endpoints_reject_non_admin(test_client) -> None:
    token = await _register_user(test_client, "settings-user@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    requests = [
        ("GET", "/api/settings", None),
        ("PUT", "/api/settings", {"agent_provider": "openrouter"}),
        ("POST", "/api/settings/test-key", {"provider": "openrouter", "api_key": _TEST_KEY}),
        ("POST", "/api/settings/models", {"provider": "openrouter", "api_key": _TEST_KEY}),
    ]

    for method, url, json_body in requests:
        resp = await test_client.request(method, url, json=json_body, headers=headers)
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_updates_api_key_masked_and_encrypted_at_rest(test_client) -> None:
    token = await _register_user(test_client, "settings-admin@example.com", is_admin=True)
    resp = await test_client.put(
        "/api/settings",
        json={"openrouter_key": _TEST_KEY},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["settings"]["api_keys"]["openrouter"].endswith(_TEST_KEY[-4:])
    assert body["settings"]["api_keys"]["openrouter"] != _TEST_KEY
    assert runtime_settings.get_override("api_key_openrouter") == _TEST_KEY

    async with get_db() as db:
        cursor = await db.execute("SELECT value FROM app_settings WHERE key = 'api_key_openrouter'")
        row = await cursor.fetchone()

    assert row is not None
    assert row["value"].startswith("enc:v1:")
    assert _TEST_KEY not in row["value"]


@pytest.mark.asyncio
async def test_admin_can_test_stored_key_with_generic_exception(monkeypatch, test_client) -> None:
    from backend.app.api import settings as settings_api

    token = await _register_user(test_client, "settings-admin-test@example.com", is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}
    await test_client.put("/api/settings", json={"openrouter_key": _TEST_KEY}, headers=headers)

    async def fail_provider_key(provider: str, api_key: str) -> dict:
        assert provider == "openrouter"
        assert api_key == _TEST_KEY
        raise RuntimeError(f"boom {_TEST_KEY} https://example.test/?key={_TEST_KEY}")

    monkeypatch.setattr(settings_api, "_test_provider_key", fail_provider_key)

    resp = await test_client.post(
        "/api/settings/test-key",
        json={"provider": "openrouter"},
        headers=headers,
    )

    assert resp.status_code == 200
    assert resp.json()["success"] is False
    assert resp.json()["message"] == "Unable to validate API key"
    assert _TEST_KEY not in resp.text

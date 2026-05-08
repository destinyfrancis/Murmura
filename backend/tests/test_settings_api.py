from __future__ import annotations

import httpx
import pytest

from backend.app.services import runtime_settings


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
    result = await settings_api.update_settings(req)

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
    await settings_api.update_settings(req)

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

"""Settings API — GET/PUT /api/settings, POST /api/settings/test-key.

Architecture:
  GET  /api/settings         — 返回所有設定（API keys masked）
  PUT  /api/settings         — 更新設定，寫 DB + 更新 RuntimeSettingsStore
  POST /api/settings/test-key — 測試 API key 有效性
  POST /api/settings/models   — 讀取供應商目前可用模型清單

API keys 的優先級：
  RuntimeSettingsStore (DB) > .env
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from backend.app.services.runtime_settings import get_override, set_override
from backend.app.utils.db import get_db
from backend.app.utils.logger import get_logger

router = APIRouter(prefix="/settings", tags=["settings"])
logger = get_logger("api.settings")


# ---------------------------------------------------------------------------
# Constants — known API key env var names per provider
# ---------------------------------------------------------------------------

_PROVIDER_ENV_KEYS: dict[str, str] = {
    "openrouter": "OPENROUTER_API_KEY",
    "google": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "fireworks": "FIREWORKS_API_KEY",
}

_SETTINGS_KEY_MAP: dict[str, str] = {
    # llm — global fallbacks
    "agent_provider": "agent_llm_provider",
    "agent_model": "agent_llm_model",
    "agent_model_lite": "agent_llm_model_lite",
    "report_provider": "llm_provider",
    "report_model": "report_llm_model",
    # llm — per-step overrides (Steps 1–5)
    "step1_provider": "step1_llm_provider",
    "step1_model": "step1_llm_model",
    "step2_provider": "step2_llm_provider",
    "step2_model": "step2_llm_model",
    "step3_provider": "step3_llm_provider",
    "step3_model": "step3_llm_model",
    "step3_model_lite": "step3_llm_model_lite",
    "step4_provider": "step4_llm_provider",
    "step4_model": "step4_llm_model",
    "step5_provider": "step5_llm_provider",
    "step5_model": "step5_llm_model",
    # api keys
    "openrouter_key": "api_key_openrouter",
    "google_key": "api_key_google",
    "openai_key": "api_key_openai",
    "anthropic_key": "api_key_anthropic",
    "deepseek_key": "api_key_deepseek",
    "fireworks_key": "api_key_fireworks",
    # simulation
    "default_preset": "sim_default_preset",
    "concurrency_limit": "sim_concurrency_limit",
    "default_agent_count": "sim_default_agent_count",
    "default_domain": "sim_default_domain",
    # data
    "fred_api_key": "api_key_fred",
    "external_feed_enabled": "data_external_feed_enabled",
    "feed_refresh_interval": "data_feed_refresh_interval",
}
_SETTINGS_KEY_MAP.update(
    {
        # Canonical RuntimeSettings keys accepted for external callers and
        # scripts that bypass the frontend's shorter field names.
        key: key
        for key in (
            "agent_llm_provider",
            "agent_llm_model",
            "agent_llm_model_lite",
            "llm_provider",
            "report_llm_model",
            "step1_llm_provider",
            "step1_llm_model",
            "step2_llm_provider",
            "step2_llm_model",
            "step3_llm_provider",
            "step3_llm_model",
            "step3_llm_model_lite",
            "step4_llm_provider",
            "step4_llm_model",
            "step5_llm_provider",
            "step5_llm_model",
        )
    }
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mask_key(key: str) -> str:
    """Mask an API key — show only last 4 chars: sk-or-***abc1."""
    if not key:
        return ""
    if len(key) <= 4:
        return "***"
    prefix_part = key[:6] if len(key) > 10 else ""
    suffix = key[-4:]
    if prefix_part:
        return f"{prefix_part}***{suffix}"
    return f"***{suffix}"


def _get_env_key(provider: str) -> str:
    """Return the API key for a provider from RuntimeStore → .env fallback."""
    store_key = f"api_key_{provider}"
    override = get_override(store_key)
    if override:
        return override
    env_var = _PROVIDER_ENV_KEYS.get(provider, "")
    return os.environ.get(env_var, "") if env_var else ""


def _read_setting(key: str, env_fallback_var: str = "", default: str = "") -> str:
    """Read from RuntimeStore first, then env var, then default."""
    override = get_override(key)
    if override is not None:
        return override
    if env_fallback_var:
        return os.environ.get(env_fallback_var, default)
    return default


# ---------------------------------------------------------------------------
# Response shape builder
# ---------------------------------------------------------------------------


def _build_settings_response(mask_keys: bool = True) -> dict[str, Any]:
    """Build the canonical settings response dict."""
    openrouter_key = _get_env_key("openrouter")
    google_key = _get_env_key("google")
    openai_key = _get_env_key("openai")
    anthropic_key = _get_env_key("anthropic")
    deepseek_key = _get_env_key("deepseek")
    fireworks_key = _get_env_key("fireworks")
    fred_key = _read_setting("api_key_fred", "FRED_API_KEY")

    def maybe_mask(k: str) -> str:
        return _mask_key(k) if mask_keys else k

    return {
        "llm": {
            "agent_provider": _read_setting("agent_llm_provider", "AGENT_LLM_PROVIDER", "openrouter"),
            "agent_model": _read_setting("agent_llm_model", "AGENT_LLM_MODEL", ""),
            "agent_model_lite": _read_setting("agent_llm_model_lite", "AGENT_LLM_MODEL_LITE", ""),
            "report_provider": _read_setting("llm_provider", "LLM_PROVIDER", "openrouter"),
            "report_model": _read_setting("report_llm_model", "GOOGLE_REPORT_MODEL", ""),
            # Per-step model overrides
            "steps": {
                str(s): {
                    "provider": _read_setting(f"step{s}_llm_provider", "", ""),
                    "model": _read_setting(f"step{s}_llm_model", "", ""),
                    **({"model_lite": _read_setting("step3_llm_model_lite", "", "")} if s == 3 else {}),
                }
                for s in range(1, 6)
            },
        },
        "api_keys": {
            "openrouter": maybe_mask(openrouter_key),
            "google": maybe_mask(google_key),
            "openai": maybe_mask(openai_key),
            "anthropic": maybe_mask(anthropic_key),
            "deepseek": maybe_mask(deepseek_key),
            "fireworks": maybe_mask(fireworks_key),
        },
        "simulation": {
            "default_preset": _read_setting("sim_default_preset", "", "standard"),
            "concurrency_limit": int(_read_setting("sim_concurrency_limit", "", "50")),
            "default_agent_count": int(_read_setting("sim_default_agent_count", "", "50")),
            "default_domain": _read_setting("sim_default_domain", "", "hk_city"),
        },
        "data": {
            "fred_api_key": maybe_mask(fred_key),
            "external_feed_enabled": _read_setting("data_external_feed_enabled", "EXTERNAL_FEED_ENABLED", "false") == "true",
            "feed_refresh_interval": int(_read_setting("data_feed_refresh_interval", "", "3600")),
        },
    }


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class SettingsUpdateRequest(BaseModel):
    """Body for PUT /api/settings.

    Any subset of keys may be provided; unspecified keys are untouched.
    """

    model_config = ConfigDict(extra="allow")

    # LLM config — global fallbacks
    agent_provider: str | None = None
    agent_model: str | None = None
    agent_model_lite: str | None = None
    report_provider: str | None = None
    report_model: str | None = None
    # LLM config — per-step overrides
    step1_provider: str | None = None
    step1_model: str | None = None
    step2_provider: str | None = None
    step2_model: str | None = None
    step3_provider: str | None = None
    step3_model: str | None = None
    step3_model_lite: str | None = None
    step4_provider: str | None = None
    step4_model: str | None = None
    step5_provider: str | None = None
    step5_model: str | None = None

    # API keys (plain text; we mask on read)
    openrouter_key: str | None = None
    google_key: str | None = None
    openai_key: str | None = None
    anthropic_key: str | None = None
    deepseek_key: str | None = None
    fireworks_key: str | None = None
    fred_api_key: str | None = None

    # Simulation
    default_preset: str | None = None
    concurrency_limit: int | None = None
    default_agent_count: int | None = None
    default_domain: str | None = None

    # Data feed
    external_feed_enabled: bool | None = None
    feed_refresh_interval: int | None = None


class TestKeyRequest(BaseModel):
    provider: str
    api_key: str | None = None  # None = use stored key
    model: str | None = None    # When set, send a 1-token request to verify model availability


class ProviderModelsRequest(BaseModel):
    provider: str
    api_key: str | None = None  # None = use stored key
    account_id: str | None = None  # Fireworks only; defaults to public "fireworks" account


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


async def _persist_to_db(key: str, value: str) -> None:
    """Upsert a single setting into app_settings."""
    async with get_db() as db:
        await db.execute(
            """INSERT INTO app_settings (key, value, updated_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(key) DO UPDATE SET
                   value = excluded.value,
                   updated_at = excluded.updated_at""",
            (key, value),
        )
        await db.commit()


async def _apply_update(field: str, value: Any) -> bool:
    """Map a request field → store key, persist to DB and update in-memory store."""
    store_key = _SETTINGS_KEY_MAP.get(field)
    if store_key is None:
        logger.warning("No store key mapping for field '%s'; skipping", field)
        return False
    str_value = str(value) if not isinstance(value, bool) else ("true" if value else "false")
    set_override(store_key, str_value)
    await _persist_to_db(store_key, str_value)
    logger.info("Settings: updated %s → %s", store_key, "***" if "key" in store_key else str_value)
    return True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
async def get_settings() -> dict[str, Any]:
    """Return all current settings with API keys masked."""
    return _build_settings_response(mask_keys=True)


@router.put("")
async def update_settings(req: SettingsUpdateRequest) -> dict[str, Any]:
    """Update one or more settings.  Writes to DB + RuntimeSettingsStore immediately."""
    updated: list[str] = []

    # Iterate over set fields only
    update_fields = req.model_dump(exclude_none=True)
    for field, value in (req.model_extra or {}).items():
        if value is not None:
            update_fields[field] = value

    for field, value in update_fields.items():
        if await _apply_update(field, value):
            updated.append(field)

    logger.info("Settings updated: %s", updated)
    return {"success": True, "updated": updated, "settings": _build_settings_response(mask_keys=True)}


@router.post("/test-key")
async def test_api_key(req: TestKeyRequest) -> dict[str, Any]:
    """Test whether an API key (and optionally a specific model) is valid."""
    provider = req.provider.lower()
    # Resolve key: use request value, fall back to stored key
    api_key = (req.api_key or "").strip() or _get_env_key(provider)

    if not api_key:
        raise HTTPException(status_code=400, detail="api_key is required and no stored key found")

    try:
        # Step 1: validate the API key itself
        result = await _test_provider_key(provider, api_key)
        if not result["ok"]:
            return {"success": False, "provider": provider, "message": result["message"]}

        # Step 2: if a model was specified, verify it responds
        if req.model:
            model_result = await _test_provider_model(provider, api_key, req.model)
            return {"success": model_result["ok"], "provider": provider, "message": model_result["message"]}

        return {"success": True, "provider": provider, "message": result["message"]}
    except Exception as exc:
        logger.warning("test-key failed for %s: %s", provider, exc)
        return {"success": False, "provider": provider, "message": str(exc)}


@router.post("/models")
async def list_provider_models(req: ProviderModelsRequest) -> dict[str, Any]:
    """Return a normalized model list for providers that expose catalog APIs."""
    provider = req.provider.lower()
    api_key = (req.api_key or "").strip() or _get_env_key(provider)

    if provider not in {"openrouter", "fireworks"}:
        return {
            "success": False,
            "provider": provider,
            "models": [],
            "message": f"Provider '{provider}' does not support model discovery yet",
        }
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key is required and no stored key found")

    try:
        if provider == "openrouter":
            models = await _fetch_openrouter_models(api_key)
        else:
            models = await _fetch_fireworks_models(api_key, req.account_id or "fireworks")
        return {
            "success": True,
            "provider": provider,
            "models": models,
            "message": f"Loaded {len(models)} models from {provider}",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("model discovery failed for %s: %s", provider, exc)
        return {
            "success": False,
            "provider": provider,
            "models": [],
            "message": f"Unable to load model list from {provider}",
        }


async def _test_provider_model(provider: str, api_key: str, model: str) -> dict[str, Any]:
    """Send a minimal 1-token LLM request to verify a specific model is accessible."""
    model = model.strip()
    if not model:
        return {"ok": False, "message": "Model id is required"}
    if provider == "openrouter":
        return await _test_openrouter_model(api_key, model)

    try:
        from backend.app.utils.llm_client import get_default_client  # noqa: PLC0415

        client = get_default_client()
        resp = await client.chat(
            [{"role": "user", "content": "hi"}],
            provider=provider,
            model=model,
            max_tokens=1,
            api_key=api_key,
        )
        return {"ok": True, "message": f"Model {model} accessible ✓ (via {provider})"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "message": f"Model {model} error: {str(exc)[:120]}"}


def _extract_provider_error(resp: httpx.Response) -> str:
    """Return a compact provider error message without exposing request data."""
    try:
        payload = resp.json()
    except Exception:
        text = resp.text.strip()
        return text[:160] if text else ""

    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message") or error.get("code") or ""
    elif isinstance(error, str):
        message = error
    else:
        message = payload.get("message", "")
    return str(message)[:160] if message else ""


async def _test_openrouter_model(api_key: str, model: str) -> dict[str, Any]:
    """Verify an OpenRouter model through the official chat completions API."""
    timeout = httpx.Timeout(20.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://murmura.local/settings",
                "X-Title": "Murmura Settings",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
                "temperature": 0,
            },
        )
    if resp.status_code == 200:
        return {"ok": True, "message": f"Model {model} accessible ✓ (via OpenRouter)"}

    message = _extract_provider_error(resp)
    suffix = f": {message}" if message else ""
    return {"ok": False, "message": f"Model {model} returned HTTP {resp.status_code}{suffix}"}


async def _test_provider_key(provider: str, api_key: str) -> dict[str, Any]:
    """Send a minimal request to validate the API key."""
    timeout = httpx.Timeout(10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        if provider == "openrouter":
            resp = await client.get(
                "https://openrouter.ai/api/v1/key",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                return {"ok": True, "message": "OpenRouter key valid ✓"}
            message = _extract_provider_error(resp)
            suffix = f": {message}" if message else ""
            return {"ok": False, "message": f"OpenRouter returned HTTP {resp.status_code}{suffix}"}

        elif provider == "google":
            resp = await client.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            )
            if resp.status_code == 200:
                return {"ok": True, "message": "Google API key valid ✓"}
            return {"ok": False, "message": f"Google returned HTTP {resp.status_code}"}

        elif provider == "openai":
            resp = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                return {"ok": True, "message": "OpenAI key valid ✓"}
            return {"ok": False, "message": f"OpenAI returned HTTP {resp.status_code}"}

        elif provider == "anthropic":
            # Anthropic requires a POST; use a minimal ping
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}],
                },
            )
            # 200 or 400 (bad request but authenticated) both confirm the key works
            if resp.status_code in (200, 400):
                return {"ok": True, "message": "Anthropic key valid ✓"}
            if resp.status_code == 401:
                return {"ok": False, "message": "Anthropic: invalid API key"}
            return {"ok": False, "message": f"Anthropic returned HTTP {resp.status_code}"}

        elif provider == "deepseek":
            resp = await client.get(
                "https://api.deepseek.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                return {"ok": True, "message": "DeepSeek key valid ✓"}
            return {"ok": False, "message": f"DeepSeek returned HTTP {resp.status_code}"}

        elif provider == "fireworks":
            resp = await client.get(
                "https://api.fireworks.ai/v1/accounts/fireworks/models",
                params={"filter": "supports_serverless=true", "pageSize": 1},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                return {"ok": True, "message": "Fireworks key valid ✓"}
            return {"ok": False, "message": f"Fireworks returned HTTP {resp.status_code}"}

        elif provider in ("fred", "data"):
            resp = await client.get(
                f"https://api.stlouisfed.org/fred/series?series_id=GNPCA&api_key={api_key}&file_type=json"
            )
            if resp.status_code == 200:
                return {"ok": True, "message": "FRED API key valid ✓"}
            return {"ok": False, "message": f"FRED returned HTTP {resp.status_code}"}

        else:
            return {"ok": False, "message": f"Unknown provider '{provider}' — cannot test"}


async def _fetch_openrouter_models(api_key: str) -> list[dict[str, Any]]:
    """Fetch and normalize OpenRouter model catalog entries."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        resp = await client.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        raw_models = resp.json().get("data", [])

    models: list[dict[str, Any]] = []
    for item in raw_models:
        architecture = item.get("architecture") or {}
        top_provider = item.get("top_provider") or {}
        pricing = item.get("pricing") or {}
        model_id = item.get("id", "")
        if not model_id:
            continue
        models.append(
            {
                "id": model_id,
                "name": item.get("name") or model_id,
                "description": item.get("description") or "",
                "context_length": item.get("context_length") or top_provider.get("context_length"),
                "pricing": {
                    "prompt": pricing.get("prompt"),
                    "completion": pricing.get("completion"),
                },
                "supports_tools": "tools" in (item.get("supported_parameters") or []),
                "supports_image": "image" in (architecture.get("input_modalities") or []),
            }
        )
    return sorted(models, key=lambda m: m["id"])


async def _fetch_fireworks_models(api_key: str, account_id: str) -> list[dict[str, Any]]:
    """Fetch and normalize Fireworks serverless text model catalog entries."""
    models: list[dict[str, Any]] = []
    page_token = ""
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        for _ in range(5):
            params = {
                "filter": "supports_serverless=true",
                "pageSize": 200,
            }
            if page_token:
                params["pageToken"] = page_token
            resp = await client.get(
                f"https://api.fireworks.ai/v1/accounts/{account_id}/models",
                params=params,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("models", []):
                model_id = item.get("name", "")
                if not model_id:
                    continue
                models.append(
                    {
                        "id": model_id,
                        "name": item.get("displayName") or model_id.rsplit("/", 1)[-1],
                        "description": item.get("description") or "",
                        "context_length": item.get("contextLength") or item.get("trainingContextLength"),
                        "pricing": {},
                        "supports_tools": bool(item.get("supportsTools")),
                        "supports_image": bool(item.get("supportsImageInput")),
                    }
                )
            page_token = data.get("nextPageToken") or ""
            if not page_token:
                break
    return sorted(models, key=lambda m: m["id"])

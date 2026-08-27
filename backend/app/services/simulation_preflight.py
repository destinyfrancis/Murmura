"""Pre-run readiness checks for public-beta simulation launches."""

from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any

from backend.app.config import get_settings
from backend.app.models.time_config import TimeConfig
from backend.app.services.cost_estimator import estimate_cost
from backend.app.services.runtime_settings import get_override
from backend.app.utils.db import get_db
from backend.app.utils.llm_client import _PROVIDERS, get_agent_provider_model, get_default_client
from backend.app.utils.logger import get_logger

logger = get_logger("simulation_preflight")

_KNOWN_BAD_MODELS = {
    "accounts/fireworks/models/deepseek-v3p2",
    "accounts/fireworks/models/deepseek/deepseek-v3.2",
}
_LOCAL_PROVIDERS = {"local", "vllm", "ollama"}
_MAX_AGENTS = 50_000
_MAX_ROUNDS = 100


class SimulationPreflightError(RuntimeError):
    """Raised when blocking preflight checks prevent a simulation start."""

    def __init__(self, report: dict[str, Any]) -> None:
        self.report = report
        codes = ",".join(e.get("code", "unknown") for e in report.get("blocking_errors", []))
        super().__init__(f"preflight_blocked:{codes or 'unknown'}")


class SimulationPreflightService:
    """Centralises checks needed before a simulation job is queued."""

    async def run(self, request: dict[str, Any]) -> dict[str, Any]:
        """Return a readiness report for a raw request or an existing session."""
        blocking: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        merged = await self._merge_session_request(request)
        provider, model = self._resolve_provider_model(merged, warnings)
        agent_count = _coerce_int(merged.get("agent_count"), 300)
        round_count = _coerce_int(merged.get("round_count"), 20)
        platforms = _normalise_platforms(merged.get("platforms"))
        seed_text = str(merged.get("seed_text") or "")

        capabilities = self._check_oasis(blocking)
        self._check_config(agent_count, round_count, platforms, blocking, warnings)
        cost = self._check_cost(provider, model, agent_count, round_count, blocking, warnings)
        model_check = await self._check_model(
            provider=provider,
            model=model,
            request=merged,
            blocking=blocking,
            warnings=warnings,
        )
        time_config = await self._infer_time_config(seed_text, round_count, merged, warnings)

        ready = not blocking
        return {
            "ready": ready,
            "readiness": "ready" if ready else "blocked",
            "simulation_readiness": {
                "status": "ready" if ready else "blocked",
                "blocking_count": len(blocking),
                "warning_count": len(warnings),
            },
            "blocking_errors": blocking,
            "warnings": warnings,
            "oasis": capabilities,
            "model_check": model_check,
            "cost_estimate": asdict(cost),
            "time_config": time_config.to_dict(),
            "config": {
                "agent_count": agent_count,
                "round_count": round_count,
                "platforms": platforms,
                "enabled_platforms": [p for p, enabled in platforms.items() if enabled],
                "domain_pack_id": merged.get("domain_pack_id", "hk_city"),
            },
        }

    async def run_for_session(self, session_id: str) -> dict[str, Any]:
        return await self.run({"session_id": session_id})

    async def ensure_ready_for_session(self, session_id: str) -> dict[str, Any]:
        report = await self.run_for_session(session_id)
        if not report["ready"]:
            raise SimulationPreflightError(report)
        return report

    async def _merge_session_request(self, request: dict[str, Any]) -> dict[str, Any]:
        session_id = request.get("session_id")
        if not session_id:
            merged = dict(request)
            merged["_request_model_explicit"] = bool(merged.get("llm_model") or merged.get("model"))
            if not merged.get("seed_text") and merged.get("graph_id"):
                merged["seed_text"] = await _load_seed_text(str(merged["graph_id"]))
            return merged

        async with get_db() as db:
            row = await (
                await db.execute(
                    """
                    SELECT id, seed_text, graph_id, scenario_type, agent_count, round_count,
                           llm_provider, llm_model, platforms, config_json, domain_pack_id
                    FROM simulation_sessions
                    WHERE id = ?
                    """,
                    (session_id,),
                )
            ).fetchone()
        if row is None:
            return {**request, "session_missing": True}

        import json

        try:
            config_json = json.loads(row["config_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            config_json = {}

        try:
            platforms = json.loads(row["platforms"] or "{}") or {}
        except (TypeError, json.JSONDecodeError):
            platforms = {}

        config_model = str(config_json.get("llm_model") or config_json.get("model") or "").strip()
        row_model = str(row["llm_model"] or "").strip()

        return {
            **config_json,
            "session_id": row["id"],
            "seed_text": row["seed_text"] or config_json.get("seed_text", ""),
            "graph_id": row["graph_id"] or config_json.get("graph_id", ""),
            "scenario_type": row["scenario_type"] or config_json.get("scenario_type", ""),
            "agent_count": row["agent_count"],
            "round_count": row["round_count"],
            "llm_provider": row["llm_provider"] or config_json.get("llm_provider", ""),
            "llm_model": row_model or config_model,
            "platforms": platforms or config_json.get("platforms", {}),
            "domain_pack_id": row["domain_pack_id"] or config_json.get("domain_pack_id", "hk_city"),
            "_request_model_explicit": bool(request.get("llm_model") or request.get("model")),
            "_config_model_explicit": bool(config_model),
            **request,
        }

    def _resolve_provider_model(
        self,
        request: dict[str, Any],
        warnings: list[dict[str, Any]] | None = None,
    ) -> tuple[str, str]:
        provider = str(
            request.get("llm_provider")
            or request.get("provider")
            or get_agent_provider_model()[0]
            or "openrouter"
        ).strip().lower()
        explicit_model = str(request.get("llm_model") or request.get("model") or "").strip()
        model_is_explicit = bool(request.get("_request_model_explicit") or request.get("_config_model_explicit"))
        model = explicit_model
        if not model:
            runtime_model = get_override("agent_llm_model") or os.environ.get("AGENT_LLM_MODEL", "")
            if runtime_model and runtime_model not in _KNOWN_BAD_MODELS:
                model = runtime_model
            else:
                model = _provider_default_model(provider)
                if runtime_model in _KNOWN_BAD_MODELS and warnings is not None:
                    warnings.append(_issue(
                        "model_fallback_applied",
                        f"Configured model {runtime_model} is known to fail; using provider default {model}.",
                        "Validate the replacement model in Settings before public launch gates.",
                        retryable=True,
                    ))
        if (model in _KNOWN_BAD_MODELS or _is_cross_provider_default(provider, model)) and not model_is_explicit:
            fallback_model = _provider_default_model(provider)
            if fallback_model and fallback_model not in _KNOWN_BAD_MODELS:
                if warnings is not None:
                    warnings.append(_issue(
                        "model_fallback_applied",
                        f"Stored model {model} is known to fail; using provider default {fallback_model}.",
                        "Validate the replacement model in Settings before public launch gates.",
                        retryable=True,
                    ))
                model = fallback_model
        return provider, model

    def _check_oasis(self, blocking: list[dict[str, Any]]) -> dict[str, Any]:
        from backend.app.services.oasis_compatibility import get_capabilities  # noqa: PLC0415

        capabilities = get_capabilities()
        if not bool(capabilities.get("simulation_available", capabilities.get("simulation"))):
            reason = str(capabilities.get("reason") or "unknown")
            blocking.append(_issue(
                "simulation_engine_unavailable",
                f"Simulation engine unavailable: {reason}",
                "Use Python 3.10/3.11 with OASIS installed before starting simulation.",
                retryable=False,
            ))
        return capabilities

    def _check_config(
        self,
        agent_count: int,
        round_count: int,
        platforms: dict[str, bool],
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> None:
        if agent_count < 1 or agent_count > _MAX_AGENTS:
            blocking.append(_issue(
                "invalid_agent_count",
                f"agent_count must be between 1 and {_MAX_AGENTS}",
                "Choose a supported public-beta preset or lower the agent count.",
                retryable=True,
            ))
        if round_count < 1 or round_count > _MAX_ROUNDS:
            blocking.append(_issue(
                "invalid_round_count",
                f"round_count must be between 1 and {_MAX_ROUNDS}",
                "Choose a supported public-beta preset or lower the round count.",
                retryable=True,
            ))
        if not any(platforms.values()):
            blocking.append(_issue(
                "no_platform_enabled",
                "At least one simulation platform must be enabled.",
                "Enable Twitter/X or Reddit before starting simulation.",
                retryable=True,
            ))
        experimental = [p for p in ("facebook", "instagram") if platforms.get(p)]
        if experimental:
            warnings.append(_issue(
                "experimental_platforms",
                f"Experimental platforms enabled: {', '.join(experimental)}",
                "Use Twitter/X and Reddit for launch gates; treat other platforms as beta.",
                retryable=True,
            ))

    def _check_cost(
        self,
        provider: str,
        model: str,
        agent_count: int,
        round_count: int,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> Any:
        cost = estimate_cost(provider, model, agent_count, round_count)
        hard_cap = float(os.environ.get("SESSION_COST_HARD_CAP_USD", "10.0"))
        budget = float(os.environ.get("SESSION_COST_BUDGET_USD", "5.0"))
        if cost.estimated_cost_usd > hard_cap:
            blocking.append(_issue(
                "cost_exceeds_hard_cap",
                f"Estimated cost ${cost.estimated_cost_usd:.4f} exceeds hard cap ${hard_cap:.2f}.",
                "Lower agent/round counts or raise SESSION_COST_HARD_CAP_USD.",
                retryable=True,
            ))
        elif cost.estimated_cost_usd > budget:
            warnings.append(_issue(
                "cost_exceeds_budget",
                f"Estimated cost ${cost.estimated_cost_usd:.4f} exceeds budget ${budget:.2f}.",
                "Continue only if this beta run is intentional.",
                retryable=True,
            ))
        return cost

    async def _check_model(
        self,
        *,
        provider: str,
        model: str,
        request: dict[str, Any],
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        check: dict[str, Any] = {
            "provider": provider,
            "model": model,
            "ok": True,
            "status": "static_ok",
            "live_checked": False,
            "api_key_present": False,
            "message": "Static model checks passed.",
        }
        if get_settings().DEMO_MODE:
            return {**check, "status": "demo", "message": "Demo mode does not require live model preflight."}

        if provider not in _PROVIDERS:
            check.update(ok=False, status="unknown_provider", message=f"Unknown provider '{provider}'.")
            blocking.append(_issue("unknown_provider", check["message"], "Choose a supported provider in Settings.", True))
            return check

        if not model:
            check.update(ok=False, status="missing_model", message="No model configured for agent decisions.")
            blocking.append(_issue("missing_model", check["message"], "Choose and validate a model in Settings.", True))
            return check

        if model in _KNOWN_BAD_MODELS:
            check.update(
                ok=False,
                status="known_bad_model",
                message=f"Model {model} is known to fail public-beta smoke gates.",
            )
            blocking.append(_issue(
                "known_bad_model",
                check["message"],
                "Use Settings model discovery/test-key to select an accessible model.",
                True,
            ))
            return check

        api_key = await _api_key_for(provider, request)
        check["api_key_present"] = bool(api_key)
        if provider not in _LOCAL_PROVIDERS and not api_key:
            check.update(ok=False, status="missing_api_key", message=f"Missing API key for provider '{provider}'.")
            blocking.append(_issue(
                "missing_api_key",
                check["message"],
                "Add the provider API key in Settings before starting simulation.",
                True,
            ))
            return check

        live_check = bool(request.get("live_model_check")) or os.environ.get("MURMURA_PREFLIGHT_LIVE_MODEL_CHECK") == "1"
        if not live_check:
            check["message"] = "Live model check skipped; static checks passed."
            warnings.append(_issue(
                "live_model_check_skipped",
                "Model accessibility was not verified with a live 1-token request.",
                "Run Settings → test model or set MURMURA_PREFLIGHT_LIVE_MODEL_CHECK=1 for launch gates.",
                True,
            ))
            return check

        check["live_checked"] = True
        try:
            await get_default_client().chat(
                [{"role": "user", "content": "ping"}],
                provider=provider,
                model=model,
                api_key=api_key,
                max_tokens=1,
                temperature=0,
            )
            check.update(status="live_ok", message="Model accessible via live 1-token check.")
        except Exception as exc:  # noqa: BLE001
            message = f"Model {model} is not accessible via {provider}."
            check.update(ok=False, status="live_failed", message=message, error_type=exc.__class__.__name__)
            blocking.append(_issue("model_not_accessible", message, "Pick a validated model in Settings.", True))
        return check

    async def _infer_time_config(
        self,
        seed_text: str,
        round_count: int,
        request: dict[str, Any],
        warnings: list[dict[str, Any]],
    ) -> TimeConfig:
        raw = request.get("time_config")
        if isinstance(raw, dict):
            try:
                return TimeConfig(
                    total_simulated_hours=int(raw["total_simulated_hours"]),
                    minutes_per_round=int(raw["minutes_per_round"]),
                    round_label_unit=str(raw["round_label_unit"]),
                    rationale=str(raw.get("rationale", "")),
                )
            except (KeyError, TypeError, ValueError):
                warnings.append(_issue(
                    "invalid_time_config",
                    "Stored time_config was invalid; inferred a new default.",
                    "Review the generated time scale before running.",
                    True,
                ))
        if not seed_text.strip():
            return _default_time_config(round_count)
        try:
            from backend.app.services.zero_config import ZeroConfigService  # noqa: PLC0415

            return await ZeroConfigService().infer_time_config(seed_text, round_count)
        except Exception:
            logger.warning("Preflight time config inference failed", exc_info=True)
            warnings.append(_issue(
                "time_config_fallback",
                "Time scale inference failed; using 1 day per round.",
                "Review the time scale in Step 2 before running.",
                True,
            ))
            return _default_time_config(round_count)


async def _load_seed_text(graph_id: str) -> str:
    async with get_db() as db:
        row = await (
            await db.execute(
                "SELECT seed_text FROM simulation_sessions WHERE id = ? OR graph_id = ? ORDER BY created_at DESC LIMIT 1",
                (graph_id, graph_id),
            )
        ).fetchone()
    return str(row["seed_text"] or "") if row else ""


async def _api_key_for(provider: str, request: dict[str, Any]) -> str:
    if request.get("api_key"):
        return str(request["api_key"])
    session_id = request.get("session_id")
    if session_id:
        try:
            from backend.app.services.session_key_store import SessionKeyStore  # noqa: PLC0415

            key_info = await SessionKeyStore().retrieve_key(str(session_id))
            if key_info is not None and key_info.provider == provider and key_info.api_key:
                return key_info.api_key
        except Exception:
            logger.debug("Preflight BYOK lookup skipped for session %s", session_id)

    env_key = str(_PROVIDERS.get(provider, {}).get("env_key") or "")
    return get_override(f"api_key_{provider}") or (os.environ.get(env_key, "") if env_key else "")


def _normalise_platforms(value: Any) -> dict[str, bool]:
    if isinstance(value, dict):
        return {str(k): bool(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        enabled = {str(v) for v in value}
        return {p: p in enabled for p in ("twitter", "reddit", "facebook", "instagram")}
    return {"twitter": True, "reddit": True}


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _default_time_config(round_count: int) -> TimeConfig:
    return TimeConfig(
        total_simulated_hours=max(1, round_count) * 24,
        minutes_per_round=1440,
        round_label_unit="day",
        rationale="Default: 1 day per round",
    )


def _provider_default_model(provider: str) -> str:
    return str(_PROVIDERS.get(provider, _PROVIDERS["openrouter"]).get("default_model") or "")


def _is_cross_provider_default(provider: str, model: str) -> bool:
    return provider == "fireworks" and model == _PROVIDERS["openrouter"]["default_model"]


def _issue(code: str, message: str, recommended_action: str, retryable: bool) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "recommended_action": recommended_action,
        "retryable": retryable,
    }

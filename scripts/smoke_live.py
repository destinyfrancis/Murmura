#!/usr/bin/env python3
"""Required live OASIS smoke gate: 10 agents x 1 round x Twitter+Reddit."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _selected_platforms() -> dict[str, bool]:
    raw = os.environ.get("SMOKE_LIVE_PLATFORMS", "twitter,reddit")
    selected = {part.strip().lower() for part in raw.split(",") if part.strip()}
    if not selected:
        raise RuntimeError("oasis_runtime_error: SMOKE_LIVE_PLATFORMS is empty")
    allowed = {"twitter", "reddit", "facebook", "instagram"}
    unknown = selected - allowed
    if unknown:
        raise RuntimeError(f"oasis_runtime_error: unknown smoke platform(s): {sorted(unknown)}")
    return {platform: platform in selected for platform in sorted(allowed)}


def _require_api_key() -> None:
    provider = os.environ.get("AGENT_LLM_PROVIDER") or os.environ.get("LLM_PROVIDER") or "openrouter"
    env_by_provider = {
        "openrouter": "OPENROUTER_API_KEY",
        "fireworks": "FIREWORKS_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "openai": "OPENAI_API_KEY",
        "together": "TOGETHER_API_KEY",
        "google": "GOOGLE_API_KEY",
    }
    env_key = env_by_provider.get(provider, f"{provider.upper()}_API_KEY")
    if not os.environ.get(env_key):
        raise RuntimeError(f"model_call_failed: missing required API key env {env_key} for provider {provider}")


def _record_smoke_result(payload: dict[str, object]) -> None:
    """Append a non-secret smoke result for launch-gate auditing."""
    path = Path(os.environ.get("SMOKE_LIVE_RESULTS_PATH", PROJECT_ROOT / "logs" / "smoke_live_results.jsonl"))
    path.parent.mkdir(parents=True, exist_ok=True)
    provider = os.environ.get("AGENT_LLM_PROVIDER") or os.environ.get("LLM_PROVIDER") or "openrouter"
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": os.environ.get("SMOKE_LIVE_MODEL", "") or "provider-default",
        "platforms": sorted([p for p, enabled in _selected_platforms().items() if enabled]),
        **payload,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


async def _create_live_session(platforms: dict[str, bool]) -> str:
    from backend.app.services.agent_factory import AgentFactory
    from backend.app.services.macro_controller import MacroController
    from backend.app.services.profile_generator import ProfileGenerator
    from backend.app.services.simulation_manager import (
        get_simulation_manager,
        store_agent_profiles,
    )

    graph_id = f"smoke-live-{uuid.uuid4()}"
    manager = get_simulation_manager()
    request = {
        "name": "Smoke Live Kernel Gate",
        "scenario_type": "property",
        "seed_text": "Live smoke test: small dual-platform public launch gate.",
        "agent_count": 10,
        "round_count": 1,
        "graph_id": graph_id,
        "platforms": platforms,
        "llm_provider": os.environ.get("AGENT_LLM_PROVIDER") or os.environ.get("LLM_PROVIDER") or "openrouter",
        "shocks": [
            {
                "round_number": 1,
                "shock_type": "public_narrative",
                "description": "Live gate seed post to ensure the platform has a concrete stimulus.",
                "post_content": (
                    "直播測試：政府突然公布新樓市措施，市民即時討論按揭、租金同就業風險。"
                    "請用你自己嘅背景回應呢個消息。"
                ),
            }
        ],
    }
    smoke_model = os.environ.get("SMOKE_LIVE_MODEL", "").strip()
    if smoke_model:
        request["llm_model"] = smoke_model
    session_data = await manager.create_session(request, csv_path=None)
    session_id = session_data["session_id"]
    session_dir = PROJECT_ROOT / "data" / "sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    factory = AgentFactory()
    profiles = factory.generate_population(10, None)
    macro_state = await MacroController().get_baseline_for_scenario("property")
    profile_gen = ProfileGenerator(agent_factory=factory)
    csv_path = session_dir / "agents.csv"
    csv_path.write_text(profile_gen.to_oasis_csv(profiles, macro_state), encoding="utf-8")
    await store_agent_profiles(session_id, profiles, profile_gen, macro_state)
    return session_id


async def _run_gate() -> None:
    from backend.app.services.oasis_compatibility import ensure_oasis_available
    from backend.app.services.simulation_artifacts import collect_simulation_artifacts
    from backend.app.services.simulation_manager import get_simulation_manager
    from backend.app.services.simulation_worker import get_simulation_worker
    from backend.app.utils.db import apply_migrations, init_db

    _require_api_key()
    os.environ.setdefault("MURMURA_PREFLIGHT_LIVE_MODEL_CHECK", "1")
    ensure_oasis_available()
    await init_db()
    await apply_migrations()

    platforms = _selected_platforms()
    enabled_platforms = [platform for platform, enabled in platforms.items() if enabled]
    started_at = time.monotonic()
    session_id = await _create_live_session(platforms)
    manager = get_simulation_manager()
    worker = await get_simulation_worker()
    await worker.start()
    try:
        await manager.start_session(session_id)
        deadline = asyncio.get_running_loop().time() + float(os.environ.get("SMOKE_LIVE_TIMEOUT_S", "600"))
        while asyncio.get_running_loop().time() < deadline:
            session = await manager.get_session(session_id)
            if session["status"] in {"completed", "failed"}:
                break
            await asyncio.sleep(2)
        else:
            raise RuntimeError("round_timeout: smoke-live session timed out")

        artifacts = await collect_simulation_artifacts(session_id)
        session = await manager.get_session(session_id)
        if session["status"] != "completed":
            reason = artifacts.get("failure_reason") or session.get("error_message", "")
            raise RuntimeError(f"{reason or 'oasis_runtime_error'}: session status is {session['status']}")
        if artifacts["counts"]["actions"] <= 0:
            raise RuntimeError("no_effective_actions: live smoke completed with zero effective actions")

        duration_s = time.monotonic() - started_at
        _record_smoke_result(
            {
                "status": "pass",
                "session_id": session_id,
                "rounds_completed": artifacts["rounds_completed"],
                "actions": artifacts["counts"]["actions"],
                "failure_reason": "",
                "duration_s": round(duration_s, 1),
            }
        )
        print(
            "smoke-live PASS "
            f"session_id={session_id} "
            f"rounds={artifacts['rounds_completed']} "
            f"actions={artifacts['counts']['actions']} "
            f"platforms={','.join(enabled_platforms)} "
            f"provider={os.environ.get('AGENT_LLM_PROVIDER') or os.environ.get('LLM_PROVIDER') or 'openrouter'} "
            f"model={os.environ.get('SMOKE_LIVE_MODEL', '') or 'provider-default'} "
            f"duration_s={duration_s:.1f}",
            flush=True,
        )
    finally:
        await worker.stop()


def main() -> int:
    try:
        asyncio.run(_run_gate())
        return 0
    except Exception as exc:  # noqa: BLE001
        try:
            _record_smoke_result(
                {
                    "status": "fail",
                    "session_id": "",
                    "rounds_completed": 0,
                    "actions": 0,
                    "failure_reason": str(exc),
                    "duration_s": 0,
                }
            )
        except Exception:
            pass
        print(f"smoke-live FAIL {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run and verify the 100-agent live workflow gate."""

from __future__ import annotations

import asyncio
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SEED_TEXT = """As of May 9, 2026, the United States and Iran are in a fragile and highly unstable confrontation centered on the Strait of Hormuz, maritime blockades, tanker incidents, nuclear negotiations, and regional escalation risk. A tenuous ceasefire is reportedly holding after recent U.S. strikes disabled Iranian tankers, while Washington awaits Tehran’s response to a latest proposal to end the war, reopen the Strait of Hormuz, and roll back Iran’s disputed nuclear program. Reports also describe U.S. and Gulf allies threatening sanctions if Iran does not release its hold on Hormuz shipping, while Iran seeks security guarantees, sanctions relief, recognition of peaceful enrichment rights, and limits on future U.S. or Israeli attacks. The Strait remains central because disruptions affect global oil, gas, fertilizer, shipping insurance, Gulf security, inflation expectations, and political pressure in Washington, Tehran, Gulf capitals, Beijing, Moscow, and Europe."""

PREDICTION_QUESTION = """Will the United States and Iran reach a durable de-escalation agreement within the next 30 days that reopens the Strait of Hormuz and prevents renewed direct military escalation?"""

INEFFECTIVE_ACTIONS = ("noop", "none", "do_nothing", "refresh", "sign_up")
EXPECTED_ROUNDS = 15
EXPECTED_AGENTS = 100
EXPECTED_PLATFORMS = ("twitter", "reddit")


def _load_dotenv() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _provider_env_key(provider: str) -> str:
    return {
        "openrouter": "OPENROUTER_API_KEY",
        "fireworks": "FIREWORKS_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "openai": "OPENAI_API_KEY",
        "together": "TOGETHER_API_KEY",
        "google": "GOOGLE_API_KEY",
    }.get(provider, f"{provider.upper()}_API_KEY")


def _require_live_env() -> tuple[str, str]:
    from backend.app.services.runtime_settings import get_override

    provider = (
        os.environ.get("AGENT_LLM_PROVIDER")
        or get_override("agent_llm_provider")
        or os.environ.get("LLM_PROVIDER")
        or get_override("llm_provider")
        or "openrouter"
    )
    model = os.environ.get("AGENT_LLM_MODEL") or get_override("agent_llm_model") or "deepseek/deepseek-v3.2"
    key_name = _provider_env_key(provider)
    runtime_key = get_override(f"api_key_{provider}") or ""
    if not (os.environ.get(key_name) or runtime_key):
        raise RuntimeError(f"model_call_failed: missing {key_name}/api_key_{provider} for provider {provider}")
    return provider, model


async def _load_runtime_settings() -> None:
    from backend.app.services.runtime_settings import load_from_rows, set_override
    from backend.app.utils.db import get_db

    async with get_db() as db:
        rows = await (await db.execute("SELECT key, value FROM app_settings")).fetchall()
    load_from_rows(rows)
    if os.environ.get("AGENT_LLM_PROVIDER"):
        set_override("agent_llm_provider", os.environ["AGENT_LLM_PROVIDER"])
    if os.environ.get("LLM_PROVIDER"):
        set_override("llm_provider", os.environ["LLM_PROVIDER"])
    if os.environ.get("AGENT_LLM_MODEL"):
        set_override("agent_llm_model", os.environ["AGENT_LLM_MODEL"])
        set_override("agent_llm_model_lite", os.environ["AGENT_LLM_MODEL"])
        set_override("report_llm_model", os.environ["AGENT_LLM_MODEL"])
    provider = os.environ.get("AGENT_LLM_PROVIDER") or os.environ.get("LLM_PROVIDER")
    if provider:
        key_name = _provider_env_key(provider)
        if os.environ.get(key_name):
            set_override(f"api_key_{provider}", os.environ[key_name])


async def _preflight_llm(provider: str, model: str) -> None:
    from backend.app.utils.llm_client import LLMClient

    try:
        response = await LLMClient().chat(
            [{"role": "user", "content": "Reply with OK."}],
            provider=provider,
            model=model,
            max_tokens=4,
            temperature=0,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"model_call_failed: live LLM preflight failed for {provider}/{model}: {exc}") from exc
    if not (response.content or "").strip():
        raise RuntimeError(f"model_call_failed: live LLM preflight returned empty content for {provider}/{model}")


def _run_process_check() -> list[str]:
    result = subprocess.run(
        ["pgrep", "-fl", "run_parallel_simulation|run_twitter_simulation|run_reddit_simulation"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    current_pid = str(os.getpid())
    return [line for line in lines if not line.startswith(current_pid + " ")]


async def _fetchone(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    from backend.app.utils.db import get_db

    async with get_db() as db:
        row = await (await db.execute(query, params)).fetchone()
    return dict(row) if row else None


async def _fetchall(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    from backend.app.utils.db import get_db

    async with get_db() as db:
        rows = await (await db.execute(query, params)).fetchall()
    return [dict(row) for row in rows]


def _effective_clause() -> str:
    quoted = ", ".join(f"'{item}'" for item in INEFFECTIVE_ACTIONS)
    return f"COALESCE(action_type, '') NOT IN ({quoted})"


def _verify_active_logs(session_dir: Path) -> dict[str, Any]:
    proofs: dict[str, Any] = {}
    for platform in EXPECTED_PLATFORMS:
        title = platform.capitalize()
        log_path = session_dir / f"{platform}.stderr.log"
        text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
        pattern = re.compile(
            rf"Active {title} agents this round: {EXPECTED_AGENTS}/{EXPECTED_AGENTS} round=(\d+)/{EXPECTED_ROUNDS}"
        )
        rounds = sorted({int(match.group(1)) for match in pattern.finditer(text)})
        proofs[platform] = {
            "log": str(log_path),
            "rounds": rounds,
            "ok": rounds == list(range(1, EXPECTED_ROUNDS + 1)),
        }
    return proofs


def _sqlite_tables(db_path: Path) -> set[str]:
    if not db_path.is_file():
        return set()
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return {str(row[0]) for row in rows}
    finally:
        conn.close()


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _max_len(conn: sqlite3.Connection, table: str, column: str) -> int:
    try:
        row = conn.execute(f"SELECT COALESCE(MAX(length({column})), 0) FROM {table}").fetchone()
        return int(row[0] or 0)
    except sqlite3.Error:
        return 0


def _oasis_db_metrics(session_dir: Path) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for platform in EXPECTED_PLATFORMS:
        db_path = session_dir / f"oasis_{platform}.db"
        item: dict[str, Any] = {"path": str(db_path), "exists": db_path.is_file()}
        if db_path.is_file():
            conn = sqlite3.connect(str(db_path))
            try:
                tables = _sqlite_tables(db_path)
                item["tables"] = sorted(tables)
                item["max_post_content_len"] = (
                    _max_len(conn, "post", "content") if "post" in tables and "content" in _columns(conn, "post") else 0
                )
                item["max_comment_content_len"] = (
                    _max_len(conn, "comment", "content")
                    if "comment" in tables and "content" in _columns(conn, "comment")
                    else 0
                )
                item["max_trace_info_len"] = (
                    _max_len(conn, "trace", "info") if "trace" in tables and "info" in _columns(conn, "trace") else 0
                )
                item["trace_rows"] = (
                    int(conn.execute("SELECT COUNT(*) FROM trace").fetchone()[0]) if "trace" in tables else 0
                )
            finally:
                conn.close()
        metrics[platform] = item
    return metrics


def _fallback_log_hits(session_dir: Path) -> list[dict[str, str]]:
    patterns = ("fallback", "degraded", "deterministic fallback", "timed out/failed")
    hits: list[dict[str, str]] = []
    for name in ("sim.log", "sim.stdout.log", "twitter.stderr.log", "reddit.stderr.log"):
        path = session_dir / name
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines[-400:]:
            lowered = line.lower()
            if any(pattern in lowered for pattern in patterns):
                hits.append({"source": name, "line": line[-300:]})
    return hits[:20]


async def _run_interaction(session_id: str) -> dict[str, Any]:
    first_agent = await _fetchone(
        "SELECT id, oasis_username FROM agent_profiles WHERE session_id = ? ORDER BY id LIMIT 1",
        (session_id,),
    )
    if not first_agent:
        raise RuntimeError("oasis_runtime_error: no agent available for interaction")

    from backend.app.services.interview_engine import InterviewEngine

    agent_id = str(first_agent["id"])
    response = await InterviewEngine().generate_response(
        session_id,
        agent_id,
        "你認為未來三十日內美伊能否達成持久降溫協議？請用你自己的立場回答。",
    )
    return {
        "agent_id": agent_id,
        "oasis_username": first_agent["oasis_username"],
        "response_chars": len(response or ""),
    }


async def _collect(workflow_id: str, elapsed_s: float, interaction: dict[str, Any]) -> dict[str, Any]:
    workflow = await _fetchone("SELECT * FROM workflow_runs WHERE id = ?", (workflow_id,))
    if not workflow:
        raise RuntimeError(f"oasis_runtime_error: workflow missing {workflow_id}")
    session_id = str(workflow["session_id"] or "")
    report_id = str(workflow["report_id"] or "")
    if not session_id:
        raise RuntimeError("oasis_runtime_error: workflow has no session_id")

    session = await _fetchone("SELECT * FROM simulation_sessions WHERE id = ?", (session_id,))
    job = await _fetchone(
        "SELECT * FROM simulation_jobs WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    )
    events = await _fetchall(
        "SELECT event_type, step, message, payload_json FROM workflow_events WHERE workflow_id = ? ORDER BY id",
        (workflow_id,),
    )
    counts = await _fetchone(
        f"""
        SELECT
            COUNT(*) AS total_actions,
            SUM(CASE WHEN {_effective_clause()} THEN 1 ELSE 0 END) AS effective_actions,
            SUM(CASE WHEN action_type = 'post' THEN 1 ELSE 0 END) AS posts,
            COALESCE(MAX(round_number), 0) AS max_round
        FROM simulation_actions
        WHERE session_id = ?
        """,
        (session_id,),
    )
    breakdown = await _fetchall(
        """
        SELECT platform, action_type, COUNT(*) AS count
        FROM simulation_actions
        WHERE session_id = ?
        GROUP BY platform, action_type
        ORDER BY platform, action_type
        """,
        (session_id,),
    )
    platform_totals = await _fetchall(
        f"""
        SELECT platform,
               COUNT(*) AS total_actions,
               SUM(CASE WHEN {_effective_clause()} THEN 1 ELSE 0 END) AS effective_actions,
               SUM(CASE WHEN action_type = 'post' THEN 1 ELSE 0 END) AS posts,
               COUNT(DISTINCT oasis_username) AS distinct_action_users
        FROM simulation_actions
        WHERE session_id = ?
        GROUP BY platform
        ORDER BY platform
        """,
        (session_id,),
    )
    fallback_nodes = await _fetchone(
        """
        SELECT COUNT(*) AS c
        FROM kg_nodes
        WHERE session_id = ?
          AND COALESCE(properties, '') LIKE '%workflow_fallback%'
        """,
        (str(workflow["graph_id"] or ""),),
    )

    session_dir = PROJECT_ROOT / "data" / "sessions" / session_id
    active_log_proof = _verify_active_logs(session_dir)
    event_types = [row["event_type"] for row in events]
    degraded_events = [item for item in event_types if "degraded" in str(item) or str(item) in {"internal_degraded"}]
    process_matches = _run_process_check()
    fallback_log_hits = _fallback_log_hits(session_dir)

    result = {
        "workflow_id": workflow_id,
        "session_id": session_id,
        "report_id": report_id,
        "elapsed_s": round(elapsed_s, 2),
        "workflow_status": workflow["status"],
        "simulation_session_status": session["status"] if session else None,
        "simulation_job_status": job["status"] if job else None,
        "rounds_completed": int((session or {}).get("current_round") or (counts or {}).get("max_round") or 0),
        "agent_count": int((session or {}).get("agent_count") or 0),
        "total_actions": int((counts or {}).get("total_actions") or 0),
        "effective_actions": int((counts or {}).get("effective_actions") or 0),
        "posts": int((counts or {}).get("posts") or 0),
        "platform_totals": platform_totals,
        "per_platform_action_breakdown": breakdown,
        "active_log_proof": active_log_proof,
        "oasis_db_metrics": _oasis_db_metrics(session_dir),
        "workflow_event_types": event_types,
        "degraded_events": degraded_events,
        "fallback_log_hits": fallback_log_hits,
        "fallback_graph_nodes": int((fallback_nodes or {}).get("c") or 0),
        "interaction": interaction,
        "hanging_processes": process_matches,
        "fallback_or_degraded_used": bool(
            degraded_events or fallback_log_hits or int((fallback_nodes or {}).get("c") or 0)
        ),
        "exact_env": {
            "AGENT_LLM_PROVIDER": os.environ.get("AGENT_LLM_PROVIDER", ""),
            "LLM_PROVIDER": os.environ.get("LLM_PROVIDER", ""),
            "AGENT_LLM_MODEL": os.environ.get("AGENT_LLM_MODEL", ""),
            "OASIS_ACTIVE_AGENT_LIMIT": os.environ.get("OASIS_ACTIVE_AGENT_LIMIT", "<unset>"),
            "OASIS_MODEL_MAX_TOKENS": os.environ.get("OASIS_MODEL_MAX_TOKENS", ""),
            "OASIS_LLM_TIMEOUT_S": os.environ.get("OASIS_LLM_TIMEOUT_S", ""),
            "OASIS_ROUND_TIMEOUT_S": os.environ.get("OASIS_ROUND_TIMEOUT_S", ""),
            "OASIS_PLATFORM_TIMEOUT_S": os.environ.get("OASIS_PLATFORM_TIMEOUT_S", ""),
            "SIM_TASK_TIMEOUT_S": os.environ.get("SIM_TASK_TIMEOUT_S", ""),
            "WORKFLOW_SIM_MONITOR_TIMEOUT_S": os.environ.get("WORKFLOW_SIM_MONITOR_TIMEOUT_S", ""),
            "OASIS_MAX_STORED_CONTENT_CHARS": os.environ.get("OASIS_MAX_STORED_CONTENT_CHARS", ""),
            "OASIS_MAX_TRACE_INFO_CHARS": os.environ.get("OASIS_MAX_TRACE_INFO_CHARS", ""),
            "KG_SCENARIO_TIMEOUT_S": os.environ.get("KG_SCENARIO_TIMEOUT_S", ""),
            _provider_env_key(os.environ.get("AGENT_LLM_PROVIDER", "")): "<set>",
        },
        "exact_command": "set -a; . ./.env; set +a; AGENT_LLM_PROVIDER=openrouter LLM_PROVIDER=openrouter OASIS_ACTIVE_AGENT_LIMIT=0 OASIS_MODEL_MAX_TOKENS=8192 OASIS_LLM_TIMEOUT_S=120 OASIS_ROUND_TIMEOUT_S=1800 OASIS_PLATFORM_TIMEOUT_S=3600 SIM_TASK_TIMEOUT_S=14400 WORKFLOW_SIM_MONITOR_TIMEOUT_S=14400 OASIS_MAX_STORED_CONTENT_CHARS=600 OASIS_MAX_TRACE_INFO_CHARS=1500 KG_SCENARIO_TIMEOUT_S=30 .venv311/bin/python scripts/validate_live_100_workflow.py",
    }

    failures: list[str] = []
    if result["workflow_status"] != "completed":
        failures.append("workflow status != completed")
    if result["simulation_session_status"] != "completed":
        failures.append("simulation_sessions.status != completed")
    if result["simulation_job_status"] != "completed":
        failures.append("simulation_jobs.status != completed")
    if result["rounds_completed"] != EXPECTED_ROUNDS:
        failures.append("rounds_completed != 15")
    if result["agent_count"] != EXPECTED_AGENTS:
        failures.append("agent_count != 100")
    if result["effective_actions"] <= 0:
        failures.append("effective_actions <= 0")
    for platform in EXPECTED_PLATFORMS:
        if not result["active_log_proof"][platform]["ok"]:
            failures.append(f"{platform} active log proof incomplete")
        platform_row = next((row for row in platform_totals if row["platform"] == platform), None)
        if not platform_row or int(platform_row["total_actions"] or 0) <= 0:
            failures.append(f"{platform} produced no persisted actions")
        if int(result["oasis_db_metrics"][platform].get("trace_rows") or 0) <= 0:
            failures.append(f"{platform} produced no OASIS trace rows")
    if "simulation_started" not in event_types:
        failures.append("workflow missing simulation_started")
    if "simulation_status" not in event_types or "completed" not in event_types:
        failures.append("workflow missing simulation_status/completed")
    if not report_id:
        failures.append("report_id missing")
    if process_matches:
        failures.append("hanging OASIS runner subprocesses remain")
    if result["fallback_or_degraded_used"]:
        failures.append("fallback/degraded path was used")

    result["acceptance_passed"] = not failures
    result["acceptance_failures"] = failures
    return result


async def main_async() -> int:
    _load_dotenv()
    from backend.app.services.oasis_compatibility import ensure_oasis_available, get_capabilities
    from backend.app.services.simulation_manager import get_simulation_manager
    from backend.app.services.simulation_worker import get_simulation_worker
    from backend.app.services.workflow_runner import WorkflowRunner
    from backend.app.utils.db import apply_migrations, init_db

    ensure_oasis_available()
    await init_db()
    await apply_migrations()
    await _load_runtime_settings()
    provider, model = _require_live_env()
    os.environ.setdefault("AGENT_LLM_PROVIDER", provider)
    os.environ.setdefault("LLM_PROVIDER", provider)
    os.environ.setdefault("AGENT_LLM_MODEL", model)
    os.environ.setdefault("MURMURA_STRICT_LIVE", "1")
    await _preflight_llm(provider, model)

    worker = await get_simulation_worker()
    await worker.start()
    runner = WorkflowRunner()
    start = time.perf_counter()
    workflow = await runner.create_workflow(
        seed_text=SEED_TEXT,
        scenario_question=PREDICTION_QUESTION,
        preset="fast",
    )
    workflow_id = workflow["workflow_id"]
    interaction: dict[str, Any] = {}
    result: dict[str, Any] | None = None
    try:
        await runner.run(workflow_id)
        state = await runner.get_workflow(workflow_id)
        if not state or state.get("status") != "completed":
            raise RuntimeError(f"oasis_runtime_error: workflow ended as {state.get('status') if state else 'missing'}")
        session_id = str(state.get("session_id") or "")
        interaction = await _run_interaction(session_id)
        await get_simulation_manager()._runner._subprocess_mgr.release_after_report(session_id)
        result = await _collect(workflow_id, time.perf_counter() - start, interaction)
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
        return 0 if result["acceptance_passed"] else 2
    except Exception as exc:
        elapsed_s = time.perf_counter() - start
        try:
            result = await _collect(workflow_id, elapsed_s, interaction)
        except Exception:
            result = None
        failure = {
            "acceptance_passed": False,
            "failure": str(exc),
            "workflow_id": workflow_id,
            "elapsed_s": round(elapsed_s, 2),
            "partial_result": result,
        }
        print(json.dumps(failure, ensure_ascii=False, indent=2), flush=True)
        return 1
    finally:
        await worker.stop()


def main() -> int:
    try:
        return asyncio.run(main_async())
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "acceptance_passed": False,
                    "failure": str(exc),
                    "workflow_id": "",
                    "session_id": "",
                    "report_id": "",
                },
                ensure_ascii=False,
                indent=2,
            ),
            flush=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

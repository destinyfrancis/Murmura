"""
Murmura OASIS Parallel Simulation Runner

Usage: python run_parallel_simulation.py --config /path/to/config.json

Config JSON format:
{
    "session_id": "uuid",
    "agent_csv_path": "/path/to/agents.jsonl",
    "round_count": 40,
    "platforms": {"twitter": true, "reddit": true},
    "llm_provider": "openrouter",
    "llm_model": "deepseek/deepseek-v3.2",
    "llm_api_key": "sk-...",
    "oasis_db_path": "/path/to/output.db",
    "macro_context": "...",
    "shocks": [{"round_number": 5, "shock_type": "interest_rate_hike", "post_content": "..."}]
}

Output: Writes JSONL progress updates to stdout for IPC with parent process.
Each line: {"type": "progress|post|complete|error", "data": {...}}
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import select
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from failure_contract import classify_failure

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("parallel_simulation")

# ---------------------------------------------------------------------------
# JSONL IPC output helpers
# ---------------------------------------------------------------------------
_stdout_lock = threading.Lock()


def emit(msg_type: str, data: dict[str, Any]) -> None:
    """Write a single JSONL message to stdout (thread-safe)."""
    line = json.dumps({"type": msg_type, "data": data}, ensure_ascii=False)
    with _stdout_lock:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()


def emit_progress(platform: str, round_num: int, total: int, detail: str = "") -> None:
    emit(
        "progress",
        {
            "platform": platform,
            "round": round_num,
            "total": total,
            "detail": detail,
        },
    )


def emit_error(message: str, platform: str = "parallel", code: str | None = None) -> None:
    emit("error", {"platform": platform, "code": code or classify_failure(message), "message": message})


def emit_complete(platform: str, summary: dict[str, Any]) -> None:
    emit("complete", {"platform": platform, **summary})


def _tail_file(path: Path, max_chars: int = 1200) -> str:
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text[-max_chars:]


def _platform_timeout_s(config: dict[str, Any]) -> float:
    try:
        return max(
            1.0,
            float(
                os.environ.get("OASIS_PLATFORM_TIMEOUT_S")
                or os.environ.get("OASIS_ROUND_TIMEOUT_S")
                or config.get("oasis_platform_timeout_s")
                or config.get("oasis_round_timeout_s")
                or 300
            ),
        )
    except (TypeError, ValueError):
        return 300.0


# ---------------------------------------------------------------------------
# Config loading and validation
# ---------------------------------------------------------------------------
REQUIRED_CONFIG_KEYS = frozenset(
    {
        "session_id",
        "agent_csv_path",
        "round_count",
        "platforms",
        "llm_provider",
        "llm_model",
        "oasis_db_path",
    }
)

LLM_ENV_KEYS: dict[str, str] = {
    "fireworks": "FIREWORKS_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "together": "TOGETHER_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def load_config(config_path: str) -> dict[str, Any]:
    """Load and validate configuration from a JSON file."""
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, encoding="utf-8") as f:
        config = json.load(f)

    missing = REQUIRED_CONFIG_KEYS - set(config.keys())
    if missing:
        raise ValueError(f"Missing required config keys: {sorted(missing)}")

    # Resolve llm_api_key from config or provider-specific environment.
    # SimulationRunner strips it from the written JSON for security.
    if not config.get("llm_api_key"):
        provider = str(config.get("llm_provider") or "openrouter")
        env_key = LLM_ENV_KEYS.get(provider, "OPENROUTER_API_KEY")
        config = {**config, "llm_api_key": os.environ.get(env_key, "")}

    if not Path(config["agent_csv_path"]).is_file():
        raise FileNotFoundError(f"Agent profiles file not found: {config['agent_csv_path']}")

    if config.get("round_count", 0) < 1:
        raise ValueError("round_count must be >= 1")

    return config


# ---------------------------------------------------------------------------
# Subprocess runner for platform simulations
# ---------------------------------------------------------------------------


def _run_platform_subprocess(
    script_name: str,
    platform: str,
    config: dict[str, Any],
    shutdown_event: threading.Event,
    on_progress: Callable[[str, int, dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Run a platform-specific simulation script as a subprocess.

    Reads JSONL lines from the child's stdout and re-emits them.
    Returns a summary dict on success or raises on failure.
    """
    scripts_dir = Path(__file__).resolve().parent
    script_path = scripts_dir / script_name

    if not script_path.is_file():
        raise FileNotFoundError(f"Platform script not found: {script_path}")

    # Write a temporary config file for the child process
    child_config_path = Path(config["oasis_db_path"]).parent / f"config_{platform}.json"
    child_config_path.parent.mkdir(parents=True, exist_ok=True)

    platform_db_path = Path(config["oasis_db_path"]).with_name(f"oasis_{platform}.db")
    child_config = {**config, "platform": platform, "oasis_db_path": str(platform_db_path)}
    with open(child_config_path, "w", encoding="utf-8") as f:
        json.dump(child_config, f, ensure_ascii=False)

    logger.info("Starting %s simulation subprocess: %s", platform, script_path)
    stdout_log_path = child_config_path.with_name(f"{platform}.stdout.log")
    stderr_log_path = child_config_path.with_name(f"{platform}.stderr.log")
    stderr_log = stderr_log_path.open("w", encoding="utf-8")

    proc = subprocess.Popen(
        [sys.executable, str(script_path), "--config", str(child_config_path)],
        stdout=subprocess.PIPE,
        stderr=stderr_log,
        text=True,
        bufsize=1,
    )

    collected_posts: list[dict[str, Any]] = []
    last_round = 0
    timeout_s = _platform_timeout_s(config)
    last_output_at = time.monotonic()

    try:
        assert proc.stdout is not None
        while True:
            if shutdown_event.is_set():
                proc.terminate()
                break

            if proc.poll() is not None:
                raw_line = proc.stdout.readline()
                if raw_line == "":
                    break
            else:
                ready, _, _ = select.select([proc.stdout], [], [], 1.0)
                if not ready:
                    idle_s = time.monotonic() - last_output_at
                    if idle_s > timeout_s:
                        logger.error("[%s] No output for %.0fs, killing subprocess", platform, idle_s)
                        proc.kill()
                        proc.wait()
                        stderr_log.flush()
                        raise RuntimeError(
                            f"round_timeout: {platform} simulation timed out after {timeout_s:.0f}s without output; "
                            f"stdout_log={stdout_log_path}; stderr_log={stderr_log_path}; "
                            f"stderr_tail={_tail_file(stderr_log_path)}"
                        )
                    continue
                raw_line = proc.stdout.readline()
                if raw_line == "":
                    continue

            last_output_at = time.monotonic()
            line = raw_line.strip()
            if not line:
                continue
            with stdout_log_path.open("a", encoding="utf-8") as stdout_log:
                stdout_log.write(line + "\n")

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("[%s] Non-JSON output: %s", platform, line[:200])
                continue

            msg_type = msg.get("type", "")
            msg_data = msg.get("data", {})

            if msg_type == "progress":
                last_round = msg_data.get("round", last_round)
                emit("progress", {**msg_data, "platform": platform})
                try:
                    round_num = int(last_round)
                except (TypeError, ValueError):
                    round_num = 0
                if round_num > 0 and on_progress is not None:
                    on_progress(platform, round_num, msg_data)

            elif msg_type == "post":
                collected_posts.append(msg_data)
                emit("post", {**msg_data, "platform": platform})

            elif msg_type == "action":
                emit("action", {**msg_data, "platform": platform})

            elif msg_type == "complete":
                emit("complete", {**msg_data, "platform": platform})

            elif msg_type == "error":
                emit(
                    "error",
                    {
                        **msg_data,
                        "platform": platform,
                        "code": msg_data.get("code") or classify_failure(str(msg_data)),
                    },
                )

        proc.wait(timeout=30)

    except subprocess.TimeoutExpired:
        logger.error("[%s] Subprocess timed out, killing", platform)
        proc.kill()
        proc.wait()
        stderr_log.flush()
        raise RuntimeError(
            f"round_timeout: {platform} simulation timed out; "
            f"stdout_log={stdout_log_path}; stderr_log={stderr_log_path}; "
            f"stderr_tail={_tail_file(stderr_log_path)}"
        )

    finally:
        try:
            stderr_log.close()
        except OSError:
            pass
        # Clean up temp config
        try:
            child_config_path.unlink(missing_ok=True)
        except OSError:
            pass

    if proc.returncode != 0:
        stderr_tail = _tail_file(stderr_log_path)
        logger.error("[%s] exited with code %d: %s", platform, proc.returncode, stderr_tail[:500])
        raise RuntimeError(
            f"{platform} simulation failed (exit code {proc.returncode}); "
            f"stdout_log={stdout_log_path}; stderr_log={stderr_log_path}; stderr_tail={stderr_tail[:300]}"
        )

    return {
        "platform": platform,
        "rounds_completed": last_round,
        "post_count": len(collected_posts),
    }


def _run_platform_thread(
    script_name: str,
    platform: str,
    config: dict[str, Any],
    results: dict[str, Any],
    errors: dict[str, str],
    shutdown_event: threading.Event,
    on_progress: Callable[[str, int, dict[str, Any]], None] | None = None,
) -> None:
    """Thread target that runs a platform subprocess and stores results."""
    try:
        summary = _run_platform_subprocess(
            script_name,
            platform,
            config,
            shutdown_event,
            on_progress=on_progress,
        )
        results[platform] = summary
    except Exception as exc:
        error_msg = f"{platform} simulation failed: {exc}"
        logger.error(error_msg)
        errors[platform] = error_msg
        shutdown_event.set()
        emit_error(error_msg, platform=platform, code=classify_failure(exc))


# ---------------------------------------------------------------------------
# Phase 1C: network patch reader
# ---------------------------------------------------------------------------


def _read_and_consume_network_patch(session_id: str) -> list[dict[str, Any]]:
    """Read and delete network_patch.json if it exists.

    The patch file is written by NetworkEvolutionEngine.write_network_patch()
    and contains suggested follow pairs for triadic closures.  This function
    consumes it (read + delete) so it is only applied once.

    Args:
        session_id: Simulation session UUID.

    Returns:
        List of suggested_follow dicts (may be empty).
    """
    try:
        project_root = Path(__file__).resolve().parent.parent.parent
        patch_path = project_root / "data" / "sessions" / session_id / "network_patch.json"
        if not patch_path.is_file():
            return []
        content = patch_path.read_text(encoding="utf-8")
        patch_path.unlink(missing_ok=True)
        data = json.loads(content)
        follows = data.get("suggested_follows", [])
        if follows:
            logger.info(
                "[network_patch] %d suggested follows for session %s",
                len(follows),
                session_id,
            )
        return follows
    except Exception as exc:
        logger.warning("network_patch read failed for session %s: %s", session_id, exc)
        return []


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

PLATFORM_SCRIPTS = {
    "twitter": "run_twitter_simulation.py",
    "reddit": "run_reddit_simulation.py",
    "facebook": "run_facebook_simulation.py",
    "instagram": "run_instagram_simulation.py",
}


def run_parallel(config: dict[str, Any]) -> int:
    """Run enabled platform simulations in parallel threads.

    Returns a process-style exit code. Any platform-level error is fatal for
    the parent runner, because a completed session with zero actions is worse
    than a clear failed session.
    """
    platforms = config.get("platforms", {})
    enabled = [p for p, enabled in platforms.items() if enabled and p in PLATFORM_SCRIPTS]

    if not enabled:
        emit_error("No platforms enabled in config")
        return 1

    session_id = config["session_id"]
    logger.info(
        "Starting parallel simulation for session %s — platforms: %s",
        session_id,
        enabled,
    )
    # Phase 1C: consume any pending network patch before starting
    _read_and_consume_network_patch(session_id)
    emit_progress("parallel", 0, config["round_count"], f"Starting {', '.join(enabled)}")

    shutdown_event = threading.Event()
    results: dict[str, Any] = {}
    errors: dict[str, str] = {}
    threads: list[threading.Thread] = []
    progress_lock = threading.Lock()
    platform_rounds = dict.fromkeys(enabled, 0)
    aggregate_progress = {"round": 0}

    def _on_platform_progress(platform: str, round_num: int, _data: dict[str, Any]) -> None:
        """Emit a round-complete event after every enabled platform reaches it."""
        with progress_lock:
            platform_rounds[platform] = max(platform_rounds.get(platform, 0), round_num)
            completed_by_all = min(platform_rounds.values()) if platform_rounds else 0
            while aggregate_progress["round"] < completed_by_all:
                aggregate_progress["round"] += 1
                current = aggregate_progress["round"]
                emit_progress(
                    "parallel",
                    current,
                    config["round_count"],
                    f"Round {current}/{config['round_count']} complete on all platforms",
                )

    for platform in enabled:
        t = threading.Thread(
            target=_run_platform_thread,
            args=(
                PLATFORM_SCRIPTS[platform],
                platform,
                config,
                results,
                errors,
                shutdown_event,
                _on_platform_progress,
            ),
            daemon=True,
        )
        threads.append(t)
        t.start()

    # Install signal handlers for graceful shutdown
    def _handle_signal(signum: int, _frame: Any) -> None:
        logger.info("Received signal %d, shutting down", signum)
        shutdown_event.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    # Wait for all threads
    for t in threads:
        t.join()

    # Emit final summary
    if errors:
        emit(
            "error",
            {
                "platform": "parallel",
                "code": classify_failure(str(errors)),
                "message": f"Simulation completed with errors: {errors}",
                "results": results,
            },
        )
        logger.error("Parallel simulation failed. Results: %s, Errors: %s", results, errors)
        return 1
    else:
        emit(
            "complete",
            {
                "platform": "parallel",
                "session_id": session_id,
                "platforms_completed": list(results.keys()),
                "summaries": results,
            },
        )

    logger.info("Parallel simulation finished. Results: %s, Errors: %s", results, errors)
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Murmura Parallel Simulation Runner")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to simulation config JSON file",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        emit_error(f"Config error: {exc}")
        logger.error("Failed to load config: %s", exc)
        sys.exit(1)

    try:
        exit_code = run_parallel(config)
        if exit_code:
            sys.exit(exit_code)
    except Exception as exc:
        emit_error(f"Fatal error: {exc}")
        logger.exception("Unhandled exception in parallel simulation")
        sys.exit(1)


if __name__ == "__main__":
    main()

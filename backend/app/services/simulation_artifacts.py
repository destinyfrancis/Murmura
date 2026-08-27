"""Computed, non-secret simulation artifact metadata."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from backend.app.services.simulation_helpers import _PROJECT_ROOT
from backend.app.utils.db import get_db

_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)(api[_-]?key|authorization|bearer|token|secret)\s*[:=]\s*['\"]?[^'\"\s,}]+"),
)
_SESSION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}")


def sanitize_artifact_message(message: str) -> str:
    """Redact likely secrets from failure messages and log snippets."""
    sanitized = message
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub(lambda m: f"{m.group(1)}=***" if m.lastindex else "***", sanitized)
    return sanitized[:500]


def classify_failure(message: str) -> str:
    """Map raw runtime text into the public live-kernel failure contract."""
    text = message.lower()
    if "no effective" in text or "no_effective" in text or "zero effective" in text:
        return "no_effective_actions"
    if "timeout" in text or "timed out" in text:
        return "round_timeout"
    if (
        "model" in text
        or "llm" in text
        or "api" in text
        or "rate limit" in text
        or "unauthorized" in text
        or "authentication" in text
        or "401" in text
    ):
        return "model_call_failed"
    return "oasis_runtime_error"


async def count_effective_actions(session_id: str) -> int:
    """Count persisted actions that count toward the launch gate."""
    async with get_db() as db:
        row = await (
            await db.execute(
                """
                SELECT COUNT(*) AS c
                FROM simulation_actions
                WHERE session_id = ?
                  AND COALESCE(action_type, '') NOT IN ('noop', 'none', 'do_nothing', 'refresh', 'sign_up')
                """,
                (session_id,),
            )
        ).fetchone()
    return int(row["c"] if row else 0)


async def collect_simulation_artifacts(session_id: str) -> dict[str, Any]:
    """Return launch-gate artifact metadata without raw secrets."""
    session_dir = _session_directory(session_id)
    sim_config = session_dir / "sim_config.json"
    agents_csv = session_dir / "agents.csv"
    sim_log = session_dir / "sim.log"
    sim_stdout = session_dir / "sim.stdout.log"

    async with get_db() as db:
        session_row = await (
            await db.execute(
                """
                SELECT id, status, current_round, round_count, agent_count, error_message,
                       oasis_db_path, config_json
                FROM simulation_sessions
                WHERE id = ?
                """,
                (session_id,),
            )
        ).fetchone()
        if session_row is None:
            raise ValueError(f"Session not found: {session_id}")

        counts_row = await (
            await db.execute(
                """
                SELECT
                    SUM(
                        CASE
                            WHEN COALESCE(action_type, '') NOT IN ('noop', 'none', 'do_nothing')
                             AND COALESCE(action_type, '') NOT IN ('refresh', 'sign_up')
                            THEN 1 ELSE 0
                        END
                    ) AS actions,
                    SUM(CASE WHEN action_type = 'post' THEN 1 ELSE 0 END) AS posts,
                    COUNT(DISTINCT agent_id) AS active_agents,
                    COALESCE(MAX(round_number), 0) AS max_action_round
                FROM simulation_actions
                WHERE session_id = ?
                """,
                (session_id,),
            )
        ).fetchone()
        agents_row = await (
            await db.execute(
                "SELECT COUNT(*) AS c FROM agent_profiles WHERE session_id = ?",
                (session_id,),
            )
        ).fetchone()
        job_rows = await (
            await db.execute(
                """
                SELECT status, error_message, updated_at
                FROM simulation_jobs
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT 3
                """,
                (session_id,),
            )
        ).fetchall()

    errors: list[dict[str, str]] = []
    session_error = str(session_row["error_message"] or "")
    if session_error:
        errors.append(
            {
                "source": "simulation_sessions",
                "code": classify_failure(session_error),
                "message": sanitize_artifact_message(session_error),
            }
        )
    for row in job_rows:
        err = str(row["error_message"] or "")
        if err:
            errors.append(
                {
                    "source": "simulation_jobs",
                    "code": classify_failure(err),
                    "message": sanitize_artifact_message(err),
                }
            )
    for line in _tail_failure_lines(sim_log):
        errors.append(
            {
                "source": "sim_log",
                "code": classify_failure(line),
                "message": sanitize_artifact_message(line),
            }
        )
    for platform in ("twitter", "reddit"):
        for stream in ("stdout", "stderr"):
            log_path = session_dir / f"{platform}.{stream}.log"
            for line in _tail_failure_lines(log_path):
                errors.append(
                    {
                        "source": f"{platform}_{stream}",
                        "code": classify_failure(line),
                        "message": sanitize_artifact_message(line),
                    }
                )

    counts = {
        "agents": int(agents_row["c"] if agents_row else 0) or int(session_row["agent_count"] or 0),
        "actions": int(counts_row["actions"] or 0) if counts_row else 0,
        "posts": int(counts_row["posts"] or 0) if counts_row else 0,
        "errors": len(errors),
        "active_agents": int(counts_row["active_agents"] or 0) if counts_row else 0,
    }
    rounds_completed = max(
        int(session_row["current_round"] or 0),
        int(counts_row["max_action_round"] or 0) if counts_row else 0,
    )
    failure_reason = select_failure_reason(errors) if session_row["status"] == "failed" else ""
    failure_contract = _failure_contract(failure_reason)

    return {
        "session_id": session_id,
        "status": session_row["status"],
        "rounds_completed": rounds_completed,
        "failure_reason": failure_reason,
        "retryable": failure_contract["retryable"],
        "recommended_action": failure_contract["recommended_action"],
        "normalized_failure": failure_contract,
        "counts": counts,
        "artifacts": {
            "sim_config": _file_meta(sim_config),
            "agents_csv": _file_meta(_agent_csv_path(session_row, agents_csv, session_dir)),
            "sim_log": _file_meta(sim_log),
            "sim_stdout": _file_meta(sim_stdout),
            "twitter_stdout": _file_meta(session_dir / "twitter.stdout.log"),
            "twitter_stderr": _file_meta(session_dir / "twitter.stderr.log"),
            "reddit_stdout": _file_meta(session_dir / "reddit.stdout.log"),
            "reddit_stderr": _file_meta(session_dir / "reddit.stderr.log"),
            "oasis_db": _file_meta(
                _safe_session_file(session_dir, str(session_row["oasis_db_path"] or ""), session_dir / "oasis.db")
            ),
        },
        "jobs": [_job_meta(row) for row in job_rows],
        "errors": errors[:10],
    }


def _file_meta(path: Path) -> dict[str, Any]:
    exists = path.is_file()
    return {
        "path": str(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
    }


def _session_directory(session_id: str) -> Path:
    """Return a validated session directory under the project sessions root."""
    if not _SESSION_ID_PATTERN.fullmatch(session_id):
        raise ValueError("Invalid session identifier")
    sessions_root = os.path.realpath(_PROJECT_ROOT / "data" / "sessions")
    session_dir = os.path.realpath(os.path.join(sessions_root, session_id))
    if not session_dir.startswith(f"{sessions_root}{os.sep}"):
        raise ValueError("Invalid session directory")
    return Path(session_dir)


def _safe_session_file(session_dir: Path, candidate: str | Path, default: Path) -> Path:
    """Resolve a stored artifact path only when it remains inside its session."""
    candidate_path = str(candidate)
    if not os.path.isabs(candidate_path):
        candidate_path = os.path.join(_PROJECT_ROOT, candidate_path)
    session_root = os.path.realpath(session_dir)
    resolved = os.path.realpath(candidate_path)
    if resolved == session_root or not resolved.startswith(f"{session_root}{os.sep}"):
        return default
    return Path(resolved)


def _agent_csv_path(session_row: Any, default: Path, session_dir: Path) -> Path:
    try:
        config = json.loads(session_row["config_json"] or "{}")
        return _safe_session_file(session_dir, str(config.get("agent_csv_path") or default), default)
    except (TypeError, json.JSONDecodeError):
        return default


def _tail_failure_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    failure_words = ("error", "fatal", "timeout", "failed", "exception", "no effective")
    failures: list[str] = []
    for line in lines[-80:]:
        lowered = line.lower()
        if "errors: {}" in lowered:
            continue
        if any(word in lowered for word in failure_words):
            failures.append(line[-500:])
    return failures[-5:]


def _job_meta(row: Any) -> dict[str, str]:
    return {
        "status": str(row["status"] or ""),
        "error_message": sanitize_artifact_message(str(row["error_message"] or "")),
        "updated_at": str(row["updated_at"] or ""),
    }


def select_failure_reason(errors: list[dict[str, str]]) -> str:
    """Prefer the most specific live-kernel failure code."""
    for error in errors:
        code = error.get("code", "")
        if code and code != "oasis_runtime_error":
            return code
    return errors[0].get("code", "") if errors else ""


def _failure_contract(code: str) -> dict[str, Any]:
    """Return UI-facing retry guidance for normalized failures."""
    contracts = {
        "model_call_failed": {
            "retryable": True,
            "recommended_action": "Validate the provider/model in Settings, then retry the simulation.",
        },
        "no_effective_actions": {
            "retryable": True,
            "recommended_action": "Switch to a validated model or reduce the run size before retrying.",
        },
        "round_timeout": {
            "retryable": True,
            "recommended_action": "Retry with fewer agents/rounds or increase the simulation timeout.",
        },
        "oasis_runtime_error": {
            "retryable": False,
            "recommended_action": "Review simulation artifacts and backend logs before retrying.",
        },
    }
    default = {
        "retryable": False,
        "recommended_action": "No failure detected.",
    }
    selected = contracts.get(code, default)
    return {"code": code, **selected}

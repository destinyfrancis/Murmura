"""Partial per-session usage accounting. Informational only; never pauses execution.

Not all providers/subprocesses report usage. A zero total is not proof of a free run.
Legacy is_paused storage is retained for database compatibility.
"""

from __future__ import annotations

import asyncio

from backend.app.utils.logger import get_logger

logger = get_logger("cost_tracker")

_cost_lock = asyncio.Lock()
_session_costs: dict[str, float] = {}


async def record_cost(session_id: str, cost_usd: float) -> None:
    """Add *cost_usd* to the running total for *session_id*.

    Persists the updated total to the session_costs DB table (best-effort).
    """
    if not session_id:
        return
    async with _cost_lock:
        prev = _session_costs.get(session_id, 0.0)
        total = prev + cost_usd
        _session_costs[session_id] = total

    # Persist to DB (best-effort — do not block main simulation flow)
    try:
        from backend.app.utils.db import get_db  # noqa: PLC0415

        async with get_db() as db:
            await db.execute(
                """INSERT INTO session_costs (session_id, total_cost_usd, is_paused, updated_at)
                   VALUES (?, ?, ?, datetime('now'))
                   ON CONFLICT(session_id) DO UPDATE SET
                     total_cost_usd = excluded.total_cost_usd,
                     is_paused = excluded.is_paused,
                     updated_at = excluded.updated_at""",
                (session_id, total, 0),
            )
            await db.commit()
    except Exception:
        logger.warning("Failed to persist cost for session %s", session_id)


async def restore_costs_from_db() -> None:
    """Reload partial usage records from DB on app startup.

    Silently skips if the legacy ``session_costs`` table does not exist.
    """
    try:
        from backend.app.utils.db import get_db  # noqa: PLC0415

        async with get_db() as db:
            rows = await (
                await db.execute(
                    "SELECT session_id, total_cost_usd, is_paused FROM session_costs"
                )
            ).fetchall()
        for row in rows or []:
            _session_costs[row["session_id"]] = row["total_cost_usd"]
        if rows:
            logger.info("Restored cost state for %d session(s) from DB", len(rows))
    except Exception:
        logger.warning("Failed to restore costs from DB — starting with empty state")


def get_session_cost(session_id: str) -> float:
    """Return the accumulated cost for *session_id* (0.0 if unknown)."""
    return _session_costs.get(session_id, 0.0)


def clear_session(session_id: str) -> None:
    """Remove cost record for a completed session."""
    _session_costs.pop(session_id, None)

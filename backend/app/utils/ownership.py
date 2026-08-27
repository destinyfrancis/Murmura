"""Authorization helpers for session and report ownership."""

from __future__ import annotations

from fastapi import HTTPException

from backend.app.api.auth import UserProfile
from backend.app.utils.db import get_db


async def get_session_owner_id(session_id: str) -> str | None:
    """Return the owner_id for a simulation session, or raise 404."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT owner_id FROM simulation_sessions WHERE id = ?",
            (session_id,),
        )
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return row["owner_id"]


async def require_session_access(
    session_id: str,
    user: UserProfile | None,
    *,
    allow_demo_public: bool = True,
) -> None:
    """Require owner/admin access to a session.

    ``owner_id IS NULL`` is the explicit demo/anonymous policy: those sessions
    remain public when ``allow_demo_public`` is true, while owned sessions are
    only visible to their owner or an admin.
    """
    owner_id = await get_session_owner_id(session_id)
    if owner_id is None and allow_demo_public:
        return
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.is_admin or owner_id == user.id:
        return
    raise HTTPException(status_code=403, detail="Forbidden")


async def get_report_session_id(report_id: str) -> str:
    """Return the session_id for a report, or raise 404."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT session_id FROM reports WHERE id = ?",
            (report_id,),
        )
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return row["session_id"]


async def require_report_access(report_id: str, user: UserProfile | None) -> str:
    """Require owner/admin access to a report and return its session_id."""
    session_id = await get_report_session_id(report_id)
    await require_session_access(session_id, user)
    return session_id

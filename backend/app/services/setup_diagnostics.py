"""Setup diagnostics for local dev and demo readiness."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any

from backend.app.config import get_settings
from backend.app.services.oasis_compatibility import get_capabilities
from backend.app.utils.db import get_db


async def run_setup_diagnostics() -> dict[str, Any]:
    """Return actionable setup checks for Stage 11 operations."""
    settings = get_settings()
    db_ok = False
    db_error = ""
    try:
        async with get_db() as db:
            await (await db.execute("SELECT 1")).fetchone()
        db_ok = True
    except Exception as exc:  # noqa: BLE001
        db_error = str(exc)[:200]

    vector_path = Path("data/vector_store")
    api_keys = {
        "openrouter": bool(os.environ.get("OPENROUTER_API_KEY")),
        "google": bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")),
        "openai": bool(os.environ.get("OPENAI_API_KEY")),
    }
    capabilities = get_capabilities()
    checks = [
        _check("backend_api", True, "FastAPI app responded."),
        _check("db_connection", db_ok, "SQLite connection OK." if db_ok else db_error),
        _check("vector_store_path", vector_path.exists(), str(vector_path)),
        _check("oasis_dependency", bool(capabilities.get("simulation_available")), capabilities.get("reason", "")),
        _check("llm_key_configured", any(api_keys.values()), "At least one provider key is configured."),
        _check("python_version", sys.version_info[:2] in ((3, 10), (3, 11)), sys.version.split()[0]),
        _check("aiosqlite", importlib.util.find_spec("aiosqlite") is not None, "Python package import check."),
    ]
    return {
        "status": "ok" if all(c["ok"] for c in checks if c["required"]) else "degraded",
        "database_path": settings.DATABASE_PATH,
        "capabilities": capabilities,
        "api_keys": api_keys,
        "checks": checks,
    }


def _check(name: str, ok: bool, message: str, required: bool = True) -> dict[str, Any]:
    return {"name": name, "ok": ok, "message": message, "required": required}

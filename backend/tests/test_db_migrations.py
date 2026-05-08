# backend/tests/test_db_migrations.py
"""Tests for apply_migrations() idempotency."""

from __future__ import annotations

from unittest.mock import patch

import pytest


def _make_tmp_settings(tmp_path, db_name: str):
    """Return a Settings-like object pointing at a temp DB."""

    from backend.app.config import Settings

    db_file = tmp_path / db_name
    # Settings is frozen; create a fresh instance via construct (Pydantic v2)
    return Settings.model_construct(
        DATABASE_PATH=str(db_file),
        DEBUG=False,
        HOST="127.0.0.1",
        PORT=8000,
        FRONTEND_URL="http://localhost:5173",
        OASIS_PATH="",
        DEEPSEEK_API_KEY="",
        ANTHROPIC_API_KEY="",
        FIREWORKS_API_KEY="",
    )


@pytest.mark.asyncio
async def test_apply_migrations_idempotent(tmp_path):
    """Calling apply_migrations() twice must not raise."""
    import backend.app.utils.db as db_module

    fake_settings = _make_tmp_settings(tmp_path, "test.db")
    with patch.object(db_module, "get_settings", return_value=fake_settings):
        await db_module.init_db()
        await db_module.apply_migrations()
        await db_module.apply_migrations()  # second call must not raise


@pytest.mark.asyncio
async def test_tier_column_exists_after_migration(tmp_path):
    """agent_profiles table must have a tier column after migration."""
    import backend.app.utils.db as db_module

    fake_settings = _make_tmp_settings(tmp_path, "test2.db")
    with patch.object(db_module, "get_settings", return_value=fake_settings):
        await db_module.init_db()
        await db_module.apply_migrations()
        async with db_module.get_db() as db:
            cursor = await db.execute("PRAGMA table_info(agent_profiles)")
            cols = [row[1] for row in await cursor.fetchall()]
    assert "tier" in cols


@pytest.mark.asyncio
async def test_schema_contains_runtime_migrated_columns(tmp_path):
    """Fresh DB schema should include columns that startup used to add at runtime."""
    import backend.app.utils.db as db_module

    fake_settings = _make_tmp_settings(tmp_path, "test_schema_converged.db")
    with patch.object(db_module, "get_settings", return_value=fake_settings):
        await db_module.init_db()
        await db_module.apply_migrations()
        async with db_module.get_db() as db:
            session_cols = [
                row[1]
                for row in await (
                    await db.execute("PRAGMA table_info(simulation_sessions)")
                ).fetchall()
            ]
            report_cols = [row[1] for row in await (await db.execute("PRAGMA table_info(reports)")).fetchall()]
            user_cols = [row[1] for row in await (await db.execute("PRAGMA table_info(users)")).fetchall()]

    assert "domain_pack_id" in session_cols
    assert "share_token" in report_cols
    assert "is_admin" in user_cols

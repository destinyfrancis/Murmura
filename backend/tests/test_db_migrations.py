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
            agent_cols = [row[1] for row in await (await db.execute("PRAGMA table_info(agent_profiles)")).fetchall()]

    assert "domain_pack_id" in session_cols
    assert "share_token" in report_cols
    assert "is_admin" in user_cols
    assert "activity_level" in agent_cols
    assert "influence_weight" in agent_cols
    assert "is_stakeholder" in agent_cols
    assert "properties" in agent_cols


@pytest.mark.asyncio
async def test_workspace_db_runs_same_migrations(tmp_path):
    """Workspace DBs should get the same migration-managed tables/columns as global DB."""
    import backend.app.utils.db as db_module

    fake_settings = _make_tmp_settings(tmp_path, "murmura.db")
    with patch.object(db_module, "get_settings", return_value=fake_settings):
        async with db_module.get_workspace_db("workspace-a") as db:
            table_rows = await (await db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")).fetchall()
            tables = {row[0] for row in table_rows}
            kg_edge_cols = [row[1] for row in await (await db.execute("PRAGMA table_info(kg_edges)")).fetchall()]

    assert "schema_migrations" in tables
    assert "app_settings" in tables
    assert "session_costs" in tables
    assert "session_api_keys" in tables
    assert "valid_from" in kg_edge_cols
    assert "valid_until" in kg_edge_cols

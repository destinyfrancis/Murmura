"""Shared SQLite migration runner for global and workspace databases."""

from __future__ import annotations

import aiosqlite

from backend.app.utils.logger import get_logger

logger = get_logger("db.migrations")

_ALTER_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("001_agent_profiles_tier", "ALTER TABLE agent_profiles ADD COLUMN tier INTEGER DEFAULT 2"),
    ("002_agent_profiles_political_stance", "ALTER TABLE agent_profiles ADD COLUMN political_stance REAL DEFAULT 0.5"),
    ("003_kg_edges_round_number", "ALTER TABLE kg_edges ADD COLUMN round_number INTEGER NOT NULL DEFAULT 0"),
    ("004_agent_decisions_topic_tags", "ALTER TABLE agent_decisions ADD COLUMN topic_tags TEXT"),
    ("005_agent_decisions_emotional_reaction", "ALTER TABLE agent_decisions ADD COLUMN emotional_reaction TEXT"),
    ("006_agent_memories_importance_score", "ALTER TABLE agent_memories ADD COLUMN importance_score REAL DEFAULT 0.5"),
    ("007_agent_memories_metadata", "ALTER TABLE agent_memories ADD COLUMN metadata TEXT DEFAULT NULL"),
    ("008_simulation_actions_parent", "ALTER TABLE simulation_actions ADD COLUMN parent_action_id INTEGER REFERENCES simulation_actions(id)"),
    ("009_simulation_actions_engagement", "ALTER TABLE simulation_actions ADD COLUMN engagement_metrics TEXT DEFAULT '{}'"),
    ("010_sessions_owner", "ALTER TABLE simulation_sessions ADD COLUMN owner_id TEXT"),
    ("011_sessions_question", "ALTER TABLE simulation_sessions ADD COLUMN scenario_question TEXT DEFAULT ''"),
    ("012_sessions_domain_pack", "ALTER TABLE simulation_sessions ADD COLUMN domain_pack_id TEXT DEFAULT 'hk_city'"),
    ("013_reports_share_token", "ALTER TABLE reports ADD COLUMN share_token TEXT"),
    ("014_users_is_admin", "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"),
    ("015_agent_profiles_big5_openness", "ALTER TABLE agent_profiles ADD COLUMN big5_openness REAL"),
    ("016_agent_profiles_big5_conscientiousness", "ALTER TABLE agent_profiles ADD COLUMN big5_conscientiousness REAL"),
    ("017_agent_profiles_big5_extraversion", "ALTER TABLE agent_profiles ADD COLUMN big5_extraversion REAL"),
    ("018_agent_profiles_big5_agreeableness", "ALTER TABLE agent_profiles ADD COLUMN big5_agreeableness REAL"),
    ("019_agent_profiles_big5_neuroticism", "ALTER TABLE agent_profiles ADD COLUMN big5_neuroticism REAL"),
    ("020_agent_profiles_goals", "ALTER TABLE agent_profiles ADD COLUMN goals TEXT DEFAULT '[]'"),
    ("021_agent_profiles_nationality", "ALTER TABLE agent_profiles ADD COLUMN nationality TEXT DEFAULT ''"),
    ("022_kg_nodes_layer_type", "ALTER TABLE kg_nodes ADD COLUMN layer_type TEXT NOT NULL DEFAULT 'truth'"),
    ("023_kg_nodes_confidence", "ALTER TABLE kg_nodes ADD COLUMN confidence_score REAL NOT NULL DEFAULT 1.0"),
    ("024_kg_nodes_source_agent", "ALTER TABLE kg_nodes ADD COLUMN source_agent_id TEXT DEFAULT NULL"),
    ("025_kg_edges_layer_type", "ALTER TABLE kg_edges ADD COLUMN layer_type TEXT NOT NULL DEFAULT 'truth'"),
    ("026_kg_edges_confidence", "ALTER TABLE kg_edges ADD COLUMN confidence_score REAL NOT NULL DEFAULT 1.0"),
    ("027_kg_edges_source_agent", "ALTER TABLE kg_edges ADD COLUMN source_agent_id TEXT DEFAULT NULL"),
    ("028_kg_edges_source_text", "ALTER TABLE kg_edges ADD COLUMN source_text TEXT"),
    ("029_kg_edges_evidence_span", "ALTER TABLE kg_edges ADD COLUMN evidence_span TEXT"),
    ("030_market_data_granularity", "ALTER TABLE market_data ADD COLUMN granularity TEXT DEFAULT 'daily'"),
    ("031_kg_edges_valid_from", "ALTER TABLE kg_edges ADD COLUMN valid_from INTEGER DEFAULT 0"),
    ("032_kg_edges_valid_until", "ALTER TABLE kg_edges ADD COLUMN valid_until INTEGER"),
    ("033_agent_profiles_activity_level", "ALTER TABLE agent_profiles ADD COLUMN activity_level REAL DEFAULT 0.5"),
    ("034_agent_profiles_influence_weight", "ALTER TABLE agent_profiles ADD COLUMN influence_weight REAL DEFAULT 1.0"),
    ("035_agent_profiles_is_stakeholder", "ALTER TABLE agent_profiles ADD COLUMN is_stakeholder INTEGER DEFAULT 0"),
    ("036_agent_profiles_properties", "ALTER TABLE agent_profiles ADD COLUMN properties TEXT DEFAULT '{}'"),
)

_SQL_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("100_agent_interviews", "CREATE TABLE IF NOT EXISTS agent_interviews (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, agent_id TEXT NOT NULL, user_query TEXT NOT NULL, agent_response TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now')))"),
    ("101_idx_interview_session_agent", "CREATE INDEX IF NOT EXISTS idx_interview_session_agent ON agent_interviews(session_id, agent_id)"),
    ("102_idx_triple_search", "CREATE INDEX IF NOT EXISTS idx_triple_search ON memory_triples(session_id, agent_id, subject, object)"),
    ("103_session_costs", "CREATE TABLE IF NOT EXISTS session_costs (session_id TEXT PRIMARY KEY, total_cost_usd REAL NOT NULL DEFAULT 0.0, is_paused BOOLEAN NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT (datetime('now')))"),
    ("104_personality_evolution_log", "CREATE TABLE IF NOT EXISTS personality_evolution_log (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, agent_id TEXT NOT NULL, round_number INTEGER NOT NULL, trait TEXT NOT NULL, old_value REAL NOT NULL, new_value REAL NOT NULL, delta REAL NOT NULL, recorded_at TEXT NOT NULL DEFAULT (datetime('now')))"),
    ("105_idx_pel_session_round", "CREATE INDEX IF NOT EXISTS idx_pel_session_round ON personality_evolution_log(session_id, round_number)"),
    ("106_user_data_points", "CREATE TABLE IF NOT EXISTS user_data_points (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, metric TEXT NOT NULL, value REAL NOT NULL, timestamp TEXT NOT NULL, source_type TEXT NOT NULL DEFAULT 'user_file', created_at TEXT DEFAULT (datetime('now')))"),
    ("107_idx_udp_session_metric", "CREATE INDEX IF NOT EXISTS idx_udp_session_metric ON user_data_points(session_id, metric)"),
    ("108_api_data_sources", "CREATE TABLE IF NOT EXISTS api_data_sources (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, name TEXT NOT NULL, url TEXT NOT NULL, auth_header TEXT, field_mappings TEXT, last_synced_at TEXT, created_at TEXT DEFAULT (datetime('now')))"),
    ("109_idx_ads_session", "CREATE INDEX IF NOT EXISTS idx_ads_session ON api_data_sources(session_id)"),
    ("110_session_api_keys", "CREATE TABLE IF NOT EXISTS session_api_keys (session_id TEXT PRIMARY KEY, encrypted_key BLOB NOT NULL, provider TEXT NOT NULL, model TEXT, base_url TEXT, created_at TEXT DEFAULT (datetime('now')))"),
    ("111_idx_kg_edge_temporal", "CREATE INDEX IF NOT EXISTS idx_kg_edge_temporal ON kg_edges(session_id, valid_from, valid_until)"),
    ("112_app_settings", "CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT (datetime('now')))"),
)


async def apply_migrations_to_connection(db: aiosqlite.Connection) -> None:
    """Apply all idempotent migrations to an open SQLite connection."""
    await db.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )"""
    )

    for version, sql in (*_ALTER_MIGRATIONS, *_SQL_MIGRATIONS):
        if await _migration_recorded(db, version):
            continue
        try:
            await db.execute(sql)
            await _record_migration(db, version)
        except Exception as exc:
            msg = str(exc).lower()
            if "duplicate column" in msg or "already exists" in msg:
                await _record_migration(db, version)
            else:
                logger.warning("Migration %s failed: %s", version, exc)

    await db.execute("UPDATE kg_edges SET valid_from = round_number WHERE valid_from = 0 AND round_number IS NOT NULL")
    await _encrypt_plaintext_app_settings_secrets(db)
    await db.commit()


async def _migration_recorded(db: aiosqlite.Connection, version: str) -> bool:
    row = await (await db.execute("SELECT 1 FROM schema_migrations WHERE version = ?", (version,))).fetchone()
    return row is not None


async def _record_migration(db: aiosqlite.Connection, version: str) -> None:
    await db.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)", (version,))


async def _encrypt_plaintext_app_settings_secrets(db: aiosqlite.Connection) -> None:
    from backend.app.utils.secret_settings import encrypt_setting_value, is_encrypted_setting_value  # noqa: PLC0415

    rows = await (await db.execute("SELECT key, value FROM app_settings WHERE key LIKE 'api_key_%'")).fetchall()
    for row in rows:
        key = row["key"]
        value = row["value"]
        if not value or is_encrypted_setting_value(value):
            continue
        try:
            encrypted = encrypt_setting_value(key, value)
        except RuntimeError as exc:
            logger.warning("Skipping app_settings secret encryption: %s", exc)
            return
        await db.execute(
            "UPDATE app_settings SET value = ?, updated_at = datetime('now') WHERE key = ?",
            (encrypted, key),
        )

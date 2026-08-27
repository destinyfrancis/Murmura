"""
Murmura OASIS Twitter Simulation Runner

Usage: python run_twitter_simulation.py --config /path/to/config.json

Agent CSV columns: username, description, user_char
JSONL stdout IPC: {"type": "progress|post|complete|error", "data": {...}}
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import sqlite3
import sys
from pathlib import Path
from typing import Any

from failure_contract import classify_failure

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("twitter_sim")

# ---------------------------------------------------------------------------
# OASIS imports (correct top-level API)
# ---------------------------------------------------------------------------
try:
    import oasis
    from oasis import (
        ActionType,
        DefaultPlatformType,
        LLMAction,
        ManualAction,
        generate_twitter_agent_graph,
    )
except ImportError as exc:
    logger.error("OASIS not installed: %s", exc)
    print(json.dumps({"type": "error", "data": {"platform": "twitter", "message": str(exc)}}), flush=True)
    sys.exit(1)

try:
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
except ImportError as exc:
    logger.error("CAMEL-AI not installed: %s", exc)
    print(json.dumps({"type": "error", "data": {"platform": "twitter", "message": str(exc)}}), flush=True)
    sys.exit(1)

# ---------------------------------------------------------------------------
# IPC
# ---------------------------------------------------------------------------


def emit(msg_type: str, data: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps({"type": msg_type, "data": data}, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def emit_progress(current: int, total: int, detail: str = "") -> None:
    emit("progress", {"platform": "twitter", "round": current, "total": total, "detail": detail})


def emit_new_posts(db_path: str, round_num: int, last_post_id: int) -> int:
    """Read new posts from OASIS DB and emit each as a 'post' event.

    Returns the updated last_post_id (max post_id seen so far).
    """
    if not Path(db_path).exists():
        return last_post_id
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT p.post_id, p.content, u.name
               FROM post p
               LEFT JOIN user u ON p.user_id = u.user_id
               WHERE p.post_id > ?
               ORDER BY p.post_id""",
            (last_post_id,),
        ).fetchall()
        conn.close()
        for row in rows:
            content = (row["content"] or "").strip()
            if not content:
                continue
            emit(
                "post",
                {
                    "platform": "twitter",
                    "source": "agent",
                    "username": row["name"] or "Agent",
                    "content": content[:300],
                    "round": round_num,
                },
            )
        if rows:
            return max(row["post_id"] for row in rows)
    except Exception as exc:
        logger.warning("emit_new_posts failed for round %d: %s", round_num, exc)
    return last_post_id


# Content actions whose info payload may contain post text
_CONTENT_ACTIONS = frozenset(
    {
        "create_post",
        "repost",
        "quote_post",
        "create_comment",
    }
)

# All action types we track (non-content actions logged without text)
_TRACKED_ACTIONS = frozenset(
    {
        "create_post",
        "like_post",
        "unlike_post",
        "dislike_post",
        "follow",
        "unfollow",
        "repost",
        "quote_post",
        "create_comment",
        "like_comment",
        "dislike_comment",
        "do_nothing",
        "mute",
        "unmute",
        "search_posts",
        "search_user",
        "trend",
        "refresh",
    }
)


def emit_new_actions(db_path: str, round_num: int, last_trace_id: int) -> int:
    """Read new actions from OASIS trace table and emit as 'action' events.

    Non-content actions (follow, like, do_nothing, etc.) are emitted as
    ``{"type": "action", ...}`` JSONL messages so the parent process can
    track behavioral diversity beyond just posts.

    Args:
        db_path: Path to the OASIS SQLite database.
        round_num: Current simulation round number.
        last_trace_id: SQLite rowid of the last trace row processed.

    Returns:
        Updated trace rowid.
    """
    if not Path(db_path).exists():
        return last_trace_id
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT t.rowid AS trace_id, t.user_id, t.created_at, t.action, t.info, u.name
               FROM trace t
               LEFT JOIN user u ON t.user_id = u.user_id
               WHERE t.rowid > ?
               ORDER BY t.created_at""",
            (last_trace_id,),
        ).fetchall()
        conn.close()

        max_trace_id = last_trace_id
        for row in rows:
            trace_id = int(row["trace_id"] or 0)
            action = (row["action"] or "").strip()
            if action not in _TRACKED_ACTIONS:
                max_trace_id = max(max_trace_id, trace_id)
                continue
            # Skip content actions — they are already emitted via emit_new_posts
            if action in _CONTENT_ACTIONS:
                max_trace_id = max(max_trace_id, trace_id)
                continue

            username = row["name"] or f"Agent_{row['user_id']}"
            info_raw = row["info"] or "{}"
            try:
                info = json.loads(info_raw) if isinstance(info_raw, str) else {}
            except (json.JSONDecodeError, TypeError):
                info = {}

            emit(
                "action",
                {
                    "platform": "twitter",
                    "source": "agent",
                    "action_type": action,
                    "username": username,
                    "round": round_num,
                    "info": info,
                },
            )

            max_trace_id = max(max_trace_id, trace_id)

        return max_trace_id
    except Exception as exc:
        logger.warning("emit_new_actions failed for round %d: %s", round_num, exc)
    return last_trace_id


# ---------------------------------------------------------------------------
# Model builder (Fireworks AI / OpenAI-compatible)
# ---------------------------------------------------------------------------

LLM_URLS: dict[str, str] = {
    "fireworks": "https://api.fireworks.ai/inference/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "openai": "https://api.openai.com/v1",
    "together": "https://api.together.xyz/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}
LLM_ENV_KEYS: dict[str, str] = {
    "fireworks": "FIREWORKS_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "together": "TOGETHER_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def _model_max_tokens(config: dict[str, Any]) -> int:
    try:
        return max(1, int(os.environ.get("OASIS_MODEL_MAX_TOKENS") or config.get("oasis_model_max_tokens") or 1024))
    except (TypeError, ValueError):
        return 1024


def _round_timeout_s(config: dict[str, Any]) -> float:
    try:
        return max(1.0, float(os.environ.get("OASIS_ROUND_TIMEOUT_S") or config.get("oasis_round_timeout_s") or 180))
    except (TypeError, ValueError):
        return 180.0


def _llm_timeout_s(config: dict[str, Any]) -> float:
    try:
        return max(1.0, float(os.environ.get("OASIS_LLM_TIMEOUT_S") or config.get("oasis_llm_timeout_s") or 30))
    except (TypeError, ValueError):
        return 30.0


def _active_agent_limit(config: dict[str, Any], agent_count: int) -> int:
    try:
        raw = os.environ.get("OASIS_ACTIVE_AGENT_LIMIT") or config.get("oasis_active_agent_limit") or 0
        limit = int(raw)
    except (TypeError, ValueError):
        limit = 0
    if limit <= 0:
        return agent_count
    return min(agent_count, max(1, limit))


def _round_agents(all_agents: list[tuple[Any, Any]], session_id: str, round_num: int, limit: int) -> list[tuple[Any, Any]]:
    if limit >= len(all_agents):
        return all_agents
    rng = random.Random(f"{session_id}:twitter:{round_num}")
    return rng.sample(all_agents, limit)


def _stored_content_limit(config: dict[str, Any]) -> int:
    try:
        raw = os.environ.get("OASIS_MAX_STORED_CONTENT_CHARS") or config.get("oasis_max_stored_content_chars") or 800
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 800


def _trace_info_limit(config: dict[str, Any]) -> int:
    try:
        raw = os.environ.get("OASIS_MAX_TRACE_INFO_CHARS") or config.get("oasis_max_trace_info_chars") or 2000
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 2000


def _truncate_text(value: Any, limit: int) -> Any:
    if not isinstance(value, str) or limit <= 0 or len(value) <= limit:
        return value
    marker = " [truncated]"
    return value[: max(0, limit - len(marker))].rstrip() + marker


def _compact_json_value(value: Any, text_limit: int, item_limit: int = 12, depth: int = 0) -> Any:
    if depth > 4:
        return _truncate_text(str(value), text_limit)
    if isinstance(value, str):
        return _truncate_text(value, text_limit)
    if isinstance(value, list):
        compacted = [_compact_json_value(item, text_limit, item_limit, depth + 1) for item in value[:item_limit]]
        if len(value) > item_limit:
            compacted.append({"truncated_items": len(value) - item_limit})
        return compacted
    if isinstance(value, dict):
        items = list(value.items())
        compacted = {
            str(key): _compact_json_value(val, text_limit, item_limit, depth + 1)
            for key, val in items[:40]
        }
        if len(items) > 40:
            compacted["truncated_keys"] = len(items) - 40
        return compacted
    return value


def _compact_trace_info(raw_info: str | None, limit: int) -> str | None:
    if not raw_info or limit <= 0 or len(raw_info) <= limit:
        return raw_info
    try:
        payload = json.loads(raw_info)
    except (json.JSONDecodeError, TypeError):
        return json.dumps({"truncated": True, "preview": _truncate_text(raw_info, limit)}, ensure_ascii=False)

    compacted = _compact_json_value(payload, max(120, limit // 4))
    encoded = json.dumps(compacted, ensure_ascii=False, separators=(",", ":"))
    if len(encoded) <= limit:
        return encoded
    summary_limit = max(0, limit - 128)
    fallback = json.dumps(
        {"truncated": True, "action_summary": _truncate_text(encoded, summary_limit)},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    while len(fallback) > limit and summary_limit > 0:
        summary_limit = max(0, summary_limit - (len(fallback) - limit) - 8)
        fallback = json.dumps(
            {"truncated": True, "action_summary": _truncate_text(encoded, summary_limit)},
            ensure_ascii=False,
            separators=(",", ":"),
        )
    return fallback if len(fallback) <= limit else '{"truncated":true}'


def _prune_visible_content(db_path: str, config: dict[str, Any]) -> None:
    """Keep OASIS-visible history small enough for later LLM rounds."""
    if not Path(db_path).exists():
        return
    content_limit = _stored_content_limit(config)
    trace_limit = _trace_info_limit(config)
    if content_limit <= 0 and trace_limit <= 0:
        return

    try:
        conn = sqlite3.connect(db_path, timeout=10)
        if content_limit > 0:
            for table, column in (
                ("post", "content"),
                ("post", "quote_content"),
                ("comment", "content"),
                ("group_messages", "content"),
            ):
                try:
                    conn.execute(
                        f"UPDATE {table} SET {column} = substr({column}, 1, ?) "
                        f"WHERE {column} IS NOT NULL AND length({column}) > ?",
                        (content_limit, content_limit),
                    )
                except sqlite3.Error:
                    continue
        if trace_limit > 0:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT rowid AS trace_id, info FROM trace WHERE info IS NOT NULL AND length(info) > ?",
                (trace_limit,),
            ).fetchall()
            for row in rows:
                conn.execute(
                    "UPDATE trace SET info = ? WHERE rowid = ?",
                    (_compact_trace_info(row["info"], trace_limit), int(row["trace_id"])),
                )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.warning("prune_visible_content failed: %s", exc)


def build_model(config: dict[str, Any]) -> Any:
    provider = config.get("llm_provider", "openrouter")
    model_name = config.get("llm_model", "deepseek/deepseek-v3.2")
    if provider == "fireworks" and model_name == "deepseek/deepseek-v3.2":
        model_name = "accounts/fireworks/models/deepseek-v3p2"
    env_key = LLM_ENV_KEYS.get(provider, "OPENROUTER_API_KEY")
    api_key = config.get("llm_api_key") or os.environ.get(env_key, "") or os.environ.get("OPENROUTER_API_KEY", "")
    base_url = config.get("llm_base_url") or LLM_URLS.get(provider, "")

    if not api_key:
        raise ValueError(f"API key is required for provider '{provider}'")
    if not base_url:
        raise ValueError(f"No base_url for provider '{provider}'")

    return ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
        model_type=model_name,
        url=base_url,
        model_config_dict={"temperature": 0.7, "max_tokens": _model_max_tokens(config)},
        api_key=api_key,
        timeout=_llm_timeout_s(config),
        max_retries=1,
    )


def _max_post_id(db_path: str) -> int:
    if not Path(db_path).exists():
        return 0
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        row = conn.execute("SELECT COALESCE(MAX(post_id), 0) FROM post").fetchone()
        conn.close()
        return int(row[0] or 0)
    except Exception as exc:
        logger.warning("max_post_id failed: %s", exc)
        return 0


def _effective_action_count(db_path: str) -> int:
    """Count user-visible actions, excluding setup and passive refresh traces."""
    if not Path(db_path).exists():
        return 0
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        row = conn.execute(
            "SELECT COUNT(*) FROM trace WHERE action NOT IN ('sign_up', 'refresh')"
        ).fetchone()
        conn.close()
        return int(row[0] or 0)
    except Exception as exc:
        logger.warning("effective_action_count failed: %s", exc)
        return 0


# ---------------------------------------------------------------------------
# Shock injection
# ---------------------------------------------------------------------------


def get_shocks_for_round(shocks: list[dict], round_num: int) -> list[dict]:
    return [s for s in shocks if s.get("round_number") == round_num]


async def inject_shock(env: Any, agent_graph: Any, shock: dict) -> None:
    post_content = shock.get("post_content", "")
    if not post_content:
        return

    agents = agent_graph.get_agents([0])
    if not agents:
        return

    _, agent = agents[0]
    manual = ManualAction(
        action_type=ActionType.CREATE_POST,
        action_args={"content": post_content},
    )
    try:
        await env.step({agent: manual})
        logger.info("Shock '%s' injected at round %d", shock.get("shock_type", ""), shock.get("round_number", -1))
        emit(
            "post",
            {
                "platform": "twitter",
                "source": "shock",
                "username": "scenario_seed",
                "shock_type": shock.get("shock_type", ""),
                "round": shock.get("round_number", -1),
                "content": post_content[:200],
            },
        )
    except Exception as exc:
        logger.error("Shock injection failed: %s", exc)


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------

_shutdown = False


def _on_signal(signum: int, _frame: Any) -> None:
    global _shutdown
    _shutdown = True
    logger.info("Signal %d — shutting down", signum)


async def run_simulation(config: dict[str, Any]) -> None:
    global _shutdown

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    session_id = config["session_id"]
    round_count = int(config["round_count"])
    agent_csv = config["agent_csv_path"]
    db_path = config.get("oasis_db_path", f"data/twitter_{session_id}.db")
    shocks = config.get("shocks", [])

    if not Path(agent_csv).is_file():
        raise FileNotFoundError(f"Agent CSV not found: {agent_csv}")

    # Ensure db directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting — session=%s rounds=%d csv=%s", session_id, round_count, agent_csv)
    emit_progress(0, round_count, "Building LLM model")

    model = build_model(config)

    emit_progress(0, round_count, "Generating Twitter agent graph from CSV")
    agent_graph = await generate_twitter_agent_graph(
        profile_path=agent_csv,
        model=model,
        available_actions=[
            ActionType.CREATE_POST,
            ActionType.LIKE_POST,
            ActionType.DISLIKE_POST,
            ActionType.FOLLOW,
            ActionType.UNFOLLOW,
            ActionType.REPOST,
            ActionType.QUOTE_POST,
            ActionType.CREATE_COMMENT,
            ActionType.DO_NOTHING,
            ActionType.MUTE,
            ActionType.SEARCH_POSTS,
            ActionType.TREND,
        ],
    )

    agent_count = agent_graph.get_num_nodes()
    logger.info("Agent graph: %d agents", agent_count)
    emit_progress(0, round_count, f"Created {agent_count} agents")

    env = oasis.make(
        agent_graph=agent_graph,
        platform=DefaultPlatformType.TWITTER,
        database_path=db_path,
    )

    emit_progress(0, round_count, "Resetting environment")
    await env.reset()

    all_agents_list = agent_graph.get_agents()
    active_limit = _active_agent_limit(config, len(all_agents_list))
    logger.info("Active Twitter agents per round: %d/%d", active_limit, len(all_agents_list))

    total_actions = 0
    runtime_errors: list[str] = []
    last_round = 0
    last_post_id = 0
    last_trace_id = 0
    round_timeout_s = _round_timeout_s(config)

    for round_num in range(1, round_count + 1):
        last_round = round_num

        if _shutdown:
            emit_progress(round_num, round_count, "Shutdown")
            break

        # Shocks first
        for shock in get_shocks_for_round(shocks, round_num):
            await inject_shock(env, agent_graph, shock)
            last_post_id = max(last_post_id, _max_post_id(db_path))

        # Normal LLM round
        try:
            round_agents = _round_agents(all_agents_list, session_id, round_num, active_limit)
            logger.info(
                "Active Twitter agents this round: %d/%d round=%d/%d",
                len(round_agents),
                len(all_agents_list),
                round_num,
                round_count,
            )
            logger.info("Round %d/%d env.step starting", round_num, round_count)
            emit_progress(
                round_num - 1,
                round_count,
                f"Round {round_num}/{round_count} env.step starting; active agents {len(round_agents)}/{len(all_agents_list)}",
            )
            before_actions = _effective_action_count(db_path)
            llm_actions = {agent: LLMAction() for _, agent in round_agents}
            await asyncio.wait_for(env.step(llm_actions), timeout=round_timeout_s)
            _prune_visible_content(db_path, config)
            round_action_count = _effective_action_count(db_path) - before_actions
            if round_action_count <= 0:
                logger.warning("Round %d/%d produced zero effective actions", round_num, round_count)
                emit_progress(round_num, round_count, f"Round {round_num}/{round_count} done — 0 actions")
                continue
            total_actions += round_action_count
            # Emit new agent posts from OASIS DB for this round
            last_post_id = emit_new_posts(db_path, round_num, last_post_id)
            # Emit non-content actions from trace table (follow, like, lurk, etc.)
            last_trace_id = emit_new_actions(db_path, round_num, last_trace_id)
            emit_progress(
                round_num,
                round_count,
                f"Round {round_num}/{round_count} done — {round_action_count} actions",
            )
            logger.info("Round %d/%d complete", round_num, round_count)
        except Exception as exc:
            logger.error("Round %d error: %s", round_num, exc)
            runtime_errors.append(f"round {round_num}: {exc}")
            emit(
                "error",
                {
                    "platform": "twitter",
                    "round": round_num,
                    "code": classify_failure(exc),
                    "message": str(exc),
                },
            )

    if total_actions <= 0:
        raise RuntimeError("no_effective_actions: No effective LLM actions were recorded")
    if runtime_errors:
        raise RuntimeError("; ".join(runtime_errors[:3]))

    emit(
        "complete",
        {
            "platform": "twitter",
            "session_id": session_id,
            "rounds_completed": last_round,
            "total_rounds": round_count,
            "agent_count": agent_count,
            "total_actions": total_actions,
            "db_path": db_path,
        },
    )
    logger.info("Simulation complete — %d rounds, %d total actions", last_round, total_actions)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Murmura Twitter Simulation")
    parser.add_argument("--config", required=True, help="Config JSON path")
    args = parser.parse_args()

    try:
        with open(args.config, encoding="utf-8") as f:
            config = json.load(f)
    except Exception as exc:
        emit("error", {"platform": "twitter", "code": classify_failure(exc), "message": f"Config load failed: {exc}"})
        sys.exit(1)

    try:
        asyncio.run(run_simulation(config))
    except Exception as exc:
        emit("error", {"platform": "twitter", "code": classify_failure(exc), "message": f"Fatal: {exc}"})
        logger.exception("Unhandled exception")
        sys.exit(1)


if __name__ == "__main__":
    main()

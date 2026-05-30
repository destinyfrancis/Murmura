"""
Murmura OASIS Reddit Simulation Runner

Usage: python run_reddit_simulation.py --config /path/to/config.json

Runs a Reddit-style social media simulation using the OASIS framework.
Outputs JSONL progress updates to stdout for IPC with parent process.

Actions supported: CREATE_POST, UPVOTE, DOWNVOTE, CREATE_COMMENT
Agent input: CSV file with columns username, description, user_char
Reddit uses subreddits instead of hashtags; shock posts are routed to
appropriate HK-themed subreddits.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
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
logger = logging.getLogger("reddit_simulation")

# ---------------------------------------------------------------------------
# OASIS imports (with graceful fallback)
# ---------------------------------------------------------------------------

try:
    import oasis
    from oasis import (
        ActionType,
        DefaultPlatformType,
        LLMAction,
        ManualAction,
        generate_reddit_agent_graph,
    )
except ImportError as exc:
    logger.error(
        "OASIS framework not installed. "
        "Install via: pip install camel-oasis  "
        "(or ensure the oasis package is on PYTHONPATH). "
        "Original error: %s",
        exc,
    )
    print(
        json.dumps(
            {
                "type": "error",
                "data": {
                    "platform": "reddit",
                    "message": (
                        "OASIS framework not found. Install it with "
                        "'pip install camel-oasis' or add it to PYTHONPATH."
                    ),
                },
            }
        ),
        flush=True,
    )
    sys.exit(1)

try:
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
except ImportError as exc:
    logger.error(
        "CAMEL-AI not installed. Install via: pip install camel-ai. Original error: %s",
        exc,
    )
    print(
        json.dumps(
            {
                "type": "error",
                "data": {
                    "platform": "reddit",
                    "message": "CAMEL-AI not found. Install with 'pip install camel-ai'.",
                },
            }
        ),
        flush=True,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# JSONL IPC helpers
# ---------------------------------------------------------------------------


def emit(msg_type: str, data: dict[str, Any]) -> None:
    """Write a JSONL message to stdout."""
    line = json.dumps({"type": msg_type, "data": data}, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def emit_progress(round_num: int, total: int, detail: str = "") -> None:
    emit(
        "progress",
        {
            "platform": "reddit",
            "round": round_num,
            "total": total,
            "detail": detail,
        },
    )


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
_CONTENT_ACTIONS = frozenset({"create_post", "repost", "quote_post", "create_comment"})


# ---------------------------------------------------------------------------
# LLM provider mapping
# ---------------------------------------------------------------------------

LLM_PROVIDER_URLS: dict[str, str] = {
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
    rng = random.Random(f"{session_id}:reddit:{round_num}")
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
    """Create a CAMEL ModelFactory model from config."""
    provider = config.get("llm_provider", "openrouter")
    model_name = config.get("llm_model", "deepseek/deepseek-v3.2")
    if provider == "fireworks" and model_name == "deepseek/deepseek-v3.2":
        model_name = "accounts/fireworks/models/deepseek-v3p2"
    env_key = LLM_ENV_KEYS.get(provider, "OPENROUTER_API_KEY")
    api_key = config.get("llm_api_key") or os.environ.get(env_key, "") or os.environ.get("OPENROUTER_API_KEY", "")
    base_url = config.get("llm_base_url", LLM_PROVIDER_URLS.get(provider, ""))

    if not api_key:
        raise ValueError(f"API key is required for provider '{provider}'")
    if not base_url:
        raise ValueError(f"No base URL for provider '{provider}'. Set llm_base_url in config.")

    return ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
        model_type=model_name,
        url=base_url,
        model_config_dict={"temperature": 0.7, "max_tokens": _model_max_tokens(config)},
        api_key=api_key,
        timeout=_llm_timeout_s(config),
        max_retries=1,
    )


# ---------------------------------------------------------------------------
# Default subreddits for HK simulation
# ---------------------------------------------------------------------------

DEFAULT_SUBREDDITS: list[dict[str, str]] = [
    {"name": "HongKong", "description": "General Hong Kong discussion"},
    {"name": "HKProperty", "description": "Hong Kong property market discussion"},
    {"name": "HKFinance", "description": "Hong Kong finance and investment"},
    {"name": "HKPolitics", "description": "Hong Kong politics and policy"},
    {"name": "HKLife", "description": "Daily life in Hong Kong"},
    {"name": "HKJobs", "description": "Hong Kong employment and careers"},
    {"name": "HKEmigration", "description": "Emigration from Hong Kong"},
]

# Map shock types to HK subreddits
_SHOCK_SUBREDDIT_MAP: dict[str, str] = {
    "interest_rate_hike": "HKFinance",
    "property_crash": "HKProperty",
    "unemployment_spike": "HKJobs",
    "policy_change": "HKPolitics",
    "market_rally": "HKFinance",
    "emigration_wave": "HKEmigration",
}


# ---------------------------------------------------------------------------
# Profile conversion
# ---------------------------------------------------------------------------


def _reddit_profile_json_from_csv(agent_csv_path: str) -> str:
    """Convert Murmura agents.csv into camel-oasis Reddit JSON profiles."""
    csv_path = Path(agent_csv_path)
    json_path = csv_path.with_name(f"{csv_path.stem}_reddit_profiles.json")

    profiles: list[dict[str, Any]] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for idx, row in enumerate(reader):
            persona = row.get("user_char") or row.get("description") or f"Agent {idx}"
            username = row.get("username") or row.get("userid") or f"agent_{idx}"
            profiles.append(
                {
                    "username": username,
                    "bio": row.get("description") or persona[:240],
                    "persona": persona,
                    "mbti": "INTJ",
                    "gender": "unspecified",
                    "age": 35,
                    "country": "unknown",
                }
            )

    if not profiles:
        raise ValueError(f"Agent CSV contains no rows: {agent_csv_path}")

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(profiles, fh, ensure_ascii=False)

    return str(json_path)


def _effective_action_count(db_path: str) -> int:
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


def emit_new_actions(db_path: str, round_num: int, last_trace_id: int) -> int:
    """Emit new non-content Reddit trace actions as JSONL action events."""
    if not Path(db_path).exists():
        return last_trace_id
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT t.rowid AS trace_id, t.user_id, t.action, t.info, u.name
               FROM trace t
               LEFT JOIN user u ON t.user_id = u.user_id
               WHERE t.rowid > ?
               ORDER BY t.rowid""",
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
            if action in _CONTENT_ACTIONS:
                max_trace_id = max(max_trace_id, trace_id)
                continue
            info_raw = row["info"] or "{}"
            try:
                info = json.loads(info_raw) if isinstance(info_raw, str) else {}
            except (json.JSONDecodeError, TypeError):
                info = {}
            emit(
                "action",
                {
                    "platform": "reddit",
                    "source": "agent",
                    "action_type": action,
                    "username": row["name"] or f"Agent_{row['user_id']}",
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
# Shock injection
# ---------------------------------------------------------------------------


def get_shocks_for_round(shocks: list[dict[str, Any]], round_num: int) -> list[dict[str, Any]]:
    """Return shocks scheduled for the given round number."""
    return [s for s in shocks if s.get("round_number") == round_num]


async def inject_shock(env: Any, agent_graph: Any, shock: dict[str, Any]) -> None:
    """Inject a macro shock into the environment via ManualAction CREATE_POST.

    For Reddit, shocks are posted to the most relevant HK subreddit.
    """
    post_content = shock.get("post_content", "")
    if not post_content:
        logger.warning(
            "Shock at round %d has no post_content, skipping",
            shock.get("round_number"),
        )
        return

    subreddit = _SHOCK_SUBREDDIT_MAP.get(shock.get("shock_type", ""), "HongKong")
    agents = agent_graph.get_agents([0])
    if not agents:
        logger.warning("No agent available for shock injection")
        return

    _, agent = agents[0]

    try:
        manual = ManualAction(
            action_type=ActionType.CREATE_POST,
            action_args={"content": f"[r/{subreddit}] {post_content}"},
        )
        await env.step({agent: manual})
        logger.info(
            "Injected shock '%s' to r/%s at round %d",
            shock.get("shock_type", "unknown"),
            subreddit,
            shock.get("round_number", -1),
        )
        emit(
            "post",
            {
                "platform": "reddit",
                "source": "shock",
                "username": "scenario_seed",
                "shock_type": shock.get("shock_type", ""),
                "subreddit": subreddit,
                "round": shock.get("round_number", -1),
                "content": post_content[:200],
            },
        )
    except Exception as exc:
        logger.error("Failed to inject shock: %s", exc)
        emit(
            "error",
            {
                "platform": "reddit",
                "message": (f"Shock injection failed at round {shock.get('round_number')}: {exc}"),
            },
        )


# ---------------------------------------------------------------------------
# Round stats extraction
# ---------------------------------------------------------------------------


def _extract_round_stats(env: Any, round_num: int) -> dict[str, Any]:
    """Best-effort extraction of round statistics from the OASIS env."""
    stats: dict[str, Any] = {"round": round_num, "action_count": 0}

    for attr in ("last_step_actions", "action_log", "step_results"):
        log = getattr(env, attr, None)
        if log is not None:
            if isinstance(log, (list, tuple)):
                stats["action_count"] = len(log)
            elif isinstance(log, dict):
                stats["action_count"] = log.get("count", len(log))
            break

    return stats


# ---------------------------------------------------------------------------
# Main simulation (async)
# ---------------------------------------------------------------------------

_shutdown_requested = False


def _handle_signal(signum: int, _frame: Any) -> None:
    global _shutdown_requested
    logger.info("Received signal %d, requesting shutdown", signum)
    _shutdown_requested = True


async def run_reddit_simulation(config: dict[str, Any]) -> None:
    """Execute the Reddit OASIS simulation (fully async)."""
    global _shutdown_requested

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    session_id = config["session_id"]
    round_count = config["round_count"]
    agent_csv_path = config["agent_csv_path"]
    db_path = config.get("oasis_db_path", f"reddit_{session_id}.db")
    shocks = config.get("shocks", [])

    csv_file = Path(agent_csv_path)
    if not csv_file.is_file():
        raise FileNotFoundError(f"Agent CSV not found: {agent_csv_path}")

    logger.info(
        "Reddit simulation starting — session=%s, rounds=%d, csv=%s",
        session_id,
        round_count,
        agent_csv_path,
    )
    emit_progress(0, round_count, "Building OASIS Reddit model")

    # Build LLM model
    model = build_model(config)

    # Generate agent graph from CSV via the JSON profile format used by the
    # current camel-oasis Reddit helper.
    emit_progress(0, round_count, "Generating Reddit agents from CSV")
    reddit_profile_path = _reddit_profile_json_from_csv(agent_csv_path)
    agent_graph = await generate_reddit_agent_graph(
        profile_path=reddit_profile_path,
        model=model,
        available_actions=[
            ActionType.CREATE_POST,
            ActionType.LIKE_POST,
            ActionType.DISLIKE_POST,
            ActionType.CREATE_COMMENT,
            ActionType.DO_NOTHING,
            ActionType.SEARCH_POSTS,
            ActionType.TREND,
        ],
    )

    agent_count = agent_graph.get_num_nodes()
    logger.info("Agent graph built with %d agents", agent_count)

    # Create OASIS environment
    emit_progress(0, round_count, "Creating OASIS Reddit environment")

    env = oasis.make(
        agent_graph=agent_graph,
        platform=DefaultPlatformType.REDDIT,
        database_path=db_path,
    )

    logger.info("OASIS Reddit environment created — agents=%d", agent_count)
    emit_progress(0, round_count, f"Environment ready with {agent_count} agents")

    # Reset environment
    await env.reset()
    all_agents_list = agent_graph.get_agents()
    active_limit = _active_agent_limit(config, len(all_agents_list))
    logger.info("Active Reddit agents per round: %d/%d", active_limit, len(all_agents_list))

    # Run simulation rounds
    total_actions = 0
    runtime_errors: list[str] = []
    last_round = 0
    last_trace_id = 0
    round_timeout_s = _round_timeout_s(config)

    for round_num in range(1, round_count + 1):
        last_round = round_num

        if _shutdown_requested:
            logger.info("Shutdown requested, stopping at round %d", round_num)
            emit_progress(round_num, round_count, "Shutdown requested")
            break

        # Inject any scheduled shocks before stepping
        round_shocks = get_shocks_for_round(shocks, round_num)
        for shock in round_shocks:
            await inject_shock(env, agent_graph, shock)

        # Execute one simulation round
        try:
            round_agents = _round_agents(all_agents_list, session_id, round_num, active_limit)
            logger.info(
                "Active Reddit agents this round: %d/%d round=%d/%d",
                len(round_agents),
                len(all_agents_list),
                round_num,
                round_count,
            )
            logger.info("Reddit round %d/%d env.step starting", round_num, round_count)
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
                logger.warning("Reddit round %d/%d produced zero effective actions", round_num, round_count)
                emit_progress(round_num, round_count, f"Round {round_num}/{round_count} complete — 0 actions")
                continue
        except Exception as exc:
            logger.error("Error in round %d: %s", round_num, exc)
            runtime_errors.append(f"round {round_num}: {exc}")
            emit(
                "error",
                {
                    "platform": "reddit",
                    "code": classify_failure(exc),
                    "message": f"Round {round_num} failed: {exc}",
                    "round": round_num,
                },
            )
            continue

        total_actions += round_action_count
        last_trace_id = emit_new_actions(db_path, round_num, last_trace_id)

        emit_progress(round_num, round_count, f"Round {round_num}/{round_count} complete")
        logger.info(
            "Reddit round %d/%d complete — %d actions this round",
            round_num,
            round_count,
            round_action_count,
        )

    if total_actions <= 0:
        raise RuntimeError("no_effective_actions: No effective LLM actions were recorded")
    if runtime_errors:
        raise RuntimeError("; ".join(runtime_errors[:3]))

    # Final summary
    rounds_done = last_round if not _shutdown_requested else last_round - 1
    summary = {
        "platform": "reddit",
        "session_id": session_id,
        "rounds_completed": rounds_done,
        "total_rounds": round_count,
        "agent_count": agent_count,
        "total_actions": total_actions,
        "db_path": db_path,
    }

    emit("complete", summary)
    logger.info("Reddit simulation complete: %s", summary)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_config(config_path: str) -> dict[str, Any]:
    """Load config JSON from file."""
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Murmura Reddit Simulation (OASIS)")
    parser.add_argument("--config", required=True, help="Path to config JSON file")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        emit("error", {"platform": "reddit", "code": classify_failure(exc), "message": f"Config error: {exc}"})
        sys.exit(1)

    try:
        asyncio.run(run_reddit_simulation(config))
    except Exception as exc:
        emit("error", {"platform": "reddit", "code": classify_failure(exc), "message": f"Fatal error: {exc}"})
        logger.exception("Unhandled exception in Reddit simulation")
        sys.exit(1)


if __name__ == "__main__":
    main()

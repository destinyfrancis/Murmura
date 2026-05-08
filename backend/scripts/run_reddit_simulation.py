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
import signal
import sqlite3
import sys
from pathlib import Path
from typing import Any

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
        model_config_dict={"temperature": 0.7, "max_tokens": 4096},
        api_key=api_key,
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
    llm_actions = {agent: LLMAction() for _, agent in agent_graph.get_agents()}

    # Run simulation rounds
    total_actions = 0
    runtime_errors: list[str] = []
    last_round = 0

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
            before_actions = _effective_action_count(db_path)
            await env.step(llm_actions)
            round_action_count = _effective_action_count(db_path) - before_actions
            if round_action_count <= 0:
                raise RuntimeError("No effective LLM actions were recorded; model call likely failed")
        except Exception as exc:
            logger.error("Error in round %d: %s", round_num, exc)
            runtime_errors.append(f"round {round_num}: {exc}")
            emit(
                "error",
                {
                    "platform": "reddit",
                    "message": f"Round {round_num} failed: {exc}",
                    "round": round_num,
                },
            )
            continue

        total_actions += round_action_count

        emit_progress(round_num, round_count, f"Round {round_num}/{round_count} complete")
        logger.info(
            "Reddit round %d/%d complete — %d actions this round",
            round_num,
            round_count,
            round_action_count,
        )

    if runtime_errors and total_actions == 0:
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
        emit("error", {"platform": "reddit", "message": f"Config error: {exc}"})
        sys.exit(1)

    try:
        asyncio.run(run_reddit_simulation(config))
    except Exception as exc:
        emit("error", {"platform": "reddit", "message": f"Fatal error: {exc}"})
        logger.exception("Unhandled exception in Reddit simulation")
        sys.exit(1)


if __name__ == "__main__":
    main()

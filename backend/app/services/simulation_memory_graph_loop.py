"""Deterministic simulation memory and graph update loop.

This service is the zero-cost Stage 6 backbone: it turns persisted
``simulation_actions`` into agent memories, extracts rule-based triples, and
writes belief-layer KG edges.  It complements the LLM memory summariser rather
than replacing it, so dry-run/demo sessions and LLM-degraded sessions still
leave queryable memory and temporal graph traces.
"""

from __future__ import annotations

import json
import re
import zlib
from dataclasses import dataclass
from typing import Any

from backend.app.services.triple_extractor import TripleExtractor
from backend.app.utils.db import get_db
from backend.app.utils.logger import get_logger

logger = get_logger("simulation_memory_graph_loop")

_CONTENT_ACTIONS = frozenset({"post", "create_post", "create_comment", "quote_post", "repost"})
_MAX_ACTION_MEMORIES_PER_AGENT = 5
_MAX_MEMORY_TEXT_LEN = 500


@dataclass(frozen=True)
class MemoryGraphLoopStats:
    """Counts produced by one round of deterministic memory/KG processing."""

    round_number: int
    actions_seen: int
    memories_added: int
    triples_added: int
    kg_nodes_added: int
    kg_edges_added: int


class SimulationMemoryGraphLoop:
    """Backfill memories and belief KG edges from stored simulation actions."""

    def __init__(self, triple_extractor: TripleExtractor | None = None) -> None:
        self._triple_extractor = triple_extractor or TripleExtractor()

    async def process_round(self, session_id: str, round_number: int) -> MemoryGraphLoopStats:
        """Process one completed round.

        The method is idempotent at action level by storing ``action_id`` in
        ``agent_memories.metadata`` and checking for it before insert.
        """
        actions = await self._load_content_actions(session_id, round_number)
        if not actions:
            return MemoryGraphLoopStats(round_number, 0, 0, 0, 0, 0)

        memories_added = 0
        triples_added = 0
        nodes_added = 0
        edges_added = 0
        per_agent_counts: dict[int, int] = {}

        for action in actions:
            agent_id = action.get("agent_id")
            if agent_id is None:
                continue

            current_count = per_agent_counts.get(agent_id, 0)
            if current_count >= _MAX_ACTION_MEMORIES_PER_AGENT:
                continue

            memory_id = await self._insert_memory_from_action(session_id, round_number, action)
            if memory_id is None:
                continue

            per_agent_counts[agent_id] = current_count + 1
            memories_added += 1

            triples = self._triple_extractor.extract_triples(
                action.get("content", ""),
                "observation",
                action.get("oasis_username", ""),
            )
            if triples:
                inserted = await self._insert_triples(session_id, round_number, memory_id, agent_id, triples)
                triples_added += inserted
                node_count, edge_count = await self._insert_belief_graph(session_id, round_number, agent_id, triples)
                nodes_added += node_count
                edges_added += edge_count

        stats = MemoryGraphLoopStats(
            round_number=round_number,
            actions_seen=len(actions),
            memories_added=memories_added,
            triples_added=triples_added,
            kg_nodes_added=nodes_added,
            kg_edges_added=edges_added,
        )
        logger.debug(
            "memory graph loop session=%s round=%d actions=%d memories=%d triples=%d kg_edges=%d",
            session_id,
            round_number,
            stats.actions_seen,
            stats.memories_added,
            stats.triples_added,
            stats.kg_edges_added,
        )
        return stats

    async def _load_content_actions(self, session_id: str, round_number: int) -> list[dict[str, Any]]:
        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT sa.id, sa.agent_id, sa.oasis_username, sa.action_type,
                       sa.platform, sa.content, sa.sentiment, sa.topics,
                       ap.id AS resolved_agent_id
                FROM simulation_actions sa
                LEFT JOIN agent_profiles ap
                  ON ap.session_id = sa.session_id
                 AND ap.oasis_username = sa.oasis_username
                WHERE sa.session_id = ?
                  AND sa.round_number = ?
                  AND sa.content IS NOT NULL
                  AND TRIM(sa.content) != ''
                  AND sa.action_type IN ({placeholders})
                ORDER BY sa.id
                """.format(placeholders=",".join("?" for _ in _CONTENT_ACTIONS)),
                (session_id, round_number, *_CONTENT_ACTIONS),
            )
            rows = await cursor.fetchall()

        actions: list[dict[str, Any]] = []
        for row in rows:
            agent_id = row["agent_id"] if row["agent_id"] is not None else row["resolved_agent_id"]
            actions.append(
                {
                    "id": row["id"],
                    "agent_id": agent_id,
                    "oasis_username": row["oasis_username"] or "",
                    "action_type": row["action_type"] or "post",
                    "platform": row["platform"] or "twitter",
                    "content": row["content"] or "",
                    "sentiment": row["sentiment"] or "neutral",
                    "topics": _parse_topics(row["topics"]),
                }
            )
        return actions

    async def _insert_memory_from_action(
        self,
        session_id: str,
        round_number: int,
        action: dict[str, Any],
    ) -> int | None:
        agent_id = action.get("agent_id")
        action_id = action.get("id")
        if agent_id is None or action_id is None:
            return None

        metadata = {
            "source": "simulation_action",
            "action_id": action_id,
            "platform": action.get("platform", "twitter"),
            "action_type": action.get("action_type", "post"),
            "sentiment": action.get("sentiment", "neutral"),
            "topics": action.get("topics", []),
        }
        metadata_json = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
        action_marker = f'"action_id": {action_id}'

        async with get_db() as db:
            existing = await (
                await db.execute(
                    """
                    SELECT id FROM agent_memories
                    WHERE session_id = ? AND metadata LIKE ?
                    LIMIT 1
                    """,
                    (session_id, f"%{action_marker}%"),
                )
            ).fetchone()
            if existing:
                return None

            cursor = await db.execute(
                """
                INSERT INTO agent_memories
                    (session_id, agent_id, round_number, memory_text,
                     salience_score, memory_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    agent_id,
                    round_number,
                    _memory_text(action),
                    _salience_for_action(action),
                    "observation",
                    metadata_json,
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def _insert_triples(
        self,
        session_id: str,
        round_number: int,
        memory_id: int,
        agent_id: int,
        triples: tuple[Any, ...],
    ) -> int:
        rows = [
            (
                memory_id,
                session_id,
                agent_id,
                round_number,
                t.subject,
                t.predicate,
                t.object,
                t.confidence,
            )
            for t in triples
        ]
        async with get_db() as db:
            await db.executemany(
                """
                INSERT OR IGNORE INTO memory_triples
                    (memory_id, session_id, agent_id, round_number,
                     subject, predicate, object, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            await db.commit()
        return len(rows)

    async def _insert_belief_graph(
        self,
        session_id: str,
        round_number: int,
        agent_id: int,
        triples: tuple[Any, ...],
    ) -> tuple[int, int]:
        nodes: dict[str, tuple[str, str]] = {}
        edge_rows: list[dict[str, Any]] = []

        for triple in triples:
            source_id = _belief_node_id(session_id, triple.subject)
            target_id = _belief_node_id(session_id, triple.object)
            nodes[source_id] = (triple.subject, "belief_entity")
            nodes[target_id] = (triple.object, "belief_entity")
            edge_rows.append(
                {
                    "source_id": source_id,
                    "target_id": target_id,
                    "relation_type": _kg_relation(triple.predicate),
                    "description": f"{triple.subject} {triple.predicate} {triple.object}",
                    "weight": max(0.1, min(1.0, float(triple.confidence))),
                    "source_text": f"{triple.subject} {triple.predicate} {triple.object}",
                    "evidence_span": json.dumps(
                        {"type": "memory_triple", "round": round_number, "agent_id": agent_id},
                        ensure_ascii=False,
                    ),
                }
            )

        columns = await _table_columns("kg_edges")
        has_valid_from = "valid_from" in columns

        async with get_db() as db:
            node_inserted = 0
            for node_id, (title, entity_type) in nodes.items():
                cursor = await db.execute(
                    """
                    INSERT OR IGNORE INTO kg_nodes
                        (id, session_id, entity_type, title, description,
                         properties, layer_type, confidence_score, source_agent_id)
                    VALUES (?, ?, ?, ?, ?, ?, 'belief', 0.75, ?)
                    """,
                    (
                        node_id,
                        session_id,
                        entity_type,
                        title,
                        "Simulation-derived belief entity",
                        json.dumps({"source": "simulation_memory_graph_loop"}, ensure_ascii=False),
                        str(agent_id),
                    ),
                )
                if cursor.rowcount and cursor.rowcount > 0:
                    node_inserted += 1

            edge_inserted = 0
            for edge in edge_rows:
                exists = await (
                    await db.execute(
                        """
                        SELECT id FROM kg_edges
                        WHERE session_id = ? AND source_id = ? AND target_id = ?
                          AND relation_type = ? AND round_number = ?
                          AND layer_type = 'belief' AND source_agent_id = ?
                        LIMIT 1
                        """,
                        (
                            session_id,
                            edge["source_id"],
                            edge["target_id"],
                            edge["relation_type"],
                            round_number,
                            str(agent_id),
                        ),
                    )
                ).fetchone()
                if exists:
                    continue

                if has_valid_from:
                    await db.execute(
                        """
                        INSERT INTO kg_edges
                            (session_id, source_id, target_id, relation_type,
                             description, source_text, evidence_span, weight,
                             round_number, valid_from, layer_type,
                             confidence_score, source_agent_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'belief', ?, ?)
                        """,
                        (
                            session_id,
                            edge["source_id"],
                            edge["target_id"],
                            edge["relation_type"],
                            edge["description"],
                            edge["source_text"],
                            edge["evidence_span"],
                            edge["weight"],
                            round_number,
                            round_number,
                            edge["weight"],
                            str(agent_id),
                        ),
                    )
                else:
                    await db.execute(
                        """
                        INSERT INTO kg_edges
                            (session_id, source_id, target_id, relation_type,
                             description, source_text, evidence_span, weight,
                             round_number, layer_type, confidence_score,
                             source_agent_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'belief', ?, ?)
                        """,
                        (
                            session_id,
                            edge["source_id"],
                            edge["target_id"],
                            edge["relation_type"],
                            edge["description"],
                            edge["source_text"],
                            edge["evidence_span"],
                            edge["weight"],
                            round_number,
                            edge["weight"],
                            str(agent_id),
                        ),
                    )
                edge_inserted += 1

            await db.commit()
        return node_inserted, edge_inserted


def _memory_text(action: dict[str, Any]) -> str:
    platform = action.get("platform", "twitter")
    content = str(action.get("content", "")).strip()
    if len(content) > _MAX_MEMORY_TEXT_LEN:
        content = content[: _MAX_MEMORY_TEXT_LEN - 1] + "…"
    return f"在 {platform} 發言/互動後留下記憶：{content}"


def _salience_for_action(action: dict[str, Any]) -> float:
    sentiment = action.get("sentiment", "neutral")
    if sentiment in {"positive", "negative"}:
        return 0.72
    if action.get("topics"):
        return 0.62
    return 0.5


def _parse_topics(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except Exception:
        return []
    return [str(x) for x in parsed] if isinstance(parsed, list) else []


def _belief_node_id(session_id: str, label: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_\u4e00-\u9fff]+", "_", label.strip().lower()).strip("_")
    if not slug:
        slug = "entity"
    digest = zlib.crc32(label.encode("utf-8")) & 0xFFFFFFFF
    return f"{session_id[:8]}_belief_{slug[:32]}_{digest:08x}"


def _kg_relation(predicate: str) -> str:
    mapping = {
        "worries_about": "BELIEVES_CONCERN",
        "observes": "BELIEVES_OBSERVED",
        "supports": "BELIEVES_SUPPORTS",
        "opposes": "BELIEVES_OPPOSES",
        "causes": "BELIEVES_CAUSES",
        "increases": "BELIEVES_INCREASES",
        "decreases": "BELIEVES_DECREASES",
    }
    return mapping.get(predicate, f"BELIEVES_{predicate.upper()}")


async def _table_columns(table_name: str) -> set[str]:
    async with get_db() as db:
        rows = await (await db.execute(f"PRAGMA table_info({table_name})")).fetchall()
    return {row[1] for row in rows}

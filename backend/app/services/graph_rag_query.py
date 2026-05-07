"""Structured GraphRAG retrieval over the local SQLite knowledge graph."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from backend.app.utils.db import get_db
from backend.app.utils.logger import get_logger

logger = get_logger("graph_rag_query")


@dataclass(frozen=True)
class GraphRAGQueryResult:
    """Structured retrieval result for report grounding and API responses."""

    mode: str
    query: str
    nodes: tuple[dict[str, Any], ...]
    edges: tuple[dict[str, Any], ...]
    paths: tuple[dict[str, Any], ...]
    evidence: tuple[dict[str, Any], ...]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "query": self.query,
            "nodes": list(self.nodes),
            "edges": list(self.edges),
            "paths": list(self.paths),
            "evidence": list(self.evidence),
            "confidence": self.confidence,
        }


class GraphRAGQueryService:
    """Retrieve graph structure first, with explicit degraded keyword fallback."""

    async def query(
        self,
        session_id: str,
        query: str,
        hops: int = 2,
        limit: int = 10,
        strict: bool = True,
    ) -> GraphRAGQueryResult:
        """Search entities, expand a subgraph, and return evidence metadata."""
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("query must not be empty")
        safe_hops = max(1, min(4, int(hops)))
        safe_limit = max(1, min(50, int(limit)))

        matched_nodes = await self._lookup_entities(session_id, clean_query, safe_limit)
        if not matched_nodes:
            if strict:
                return GraphRAGQueryResult(
                    mode="strict_graph_no_match",
                    query=clean_query,
                    nodes=(),
                    edges=(),
                    paths=(),
                    evidence=(),
                    confidence=0.0,
                )
            degraded = await self._degraded_keyword_search(session_id, clean_query, safe_limit)
            return GraphRAGQueryResult(
                mode="degraded_keyword_search",
                query=clean_query,
                nodes=(),
                edges=(),
                paths=(),
                evidence=tuple(degraded),
                confidence=0.25 if degraded else 0.0,
            )

        seed_ids = [n["id"] for n in matched_nodes]
        nodes, edges = await self.subgraph(session_id, seed_ids, safe_hops)
        paths: tuple[dict[str, Any], ...] = ()
        if len(seed_ids) >= 2:
            paths = tuple(await self.paths(session_id, seed_ids[0], seed_ids[1], max_hops=safe_hops + 1))

        evidence = tuple(_edge_to_evidence(edge) for edge in edges if _edge_to_evidence(edge))
        confidence = _confidence(nodes, edges, matched_nodes)
        return GraphRAGQueryResult(
            mode="graph",
            query=clean_query,
            nodes=tuple(nodes),
            edges=tuple(edges),
            paths=paths,
            evidence=evidence,
            confidence=confidence,
        )

    async def subgraph(
        self,
        session_id: str,
        seed_node_ids: list[str],
        hops: int = 2,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Return N-hop graph structure around one or more seed nodes."""
        if not seed_node_ids:
            return [], []

        visited: set[str] = set(seed_node_ids)
        frontier: set[str] = set(seed_node_ids)
        edge_by_id: dict[int, dict[str, Any]] = {}

        async with get_db() as db:
            for _ in range(max(1, min(4, hops))):
                if not frontier:
                    break
                placeholders = ",".join("?" for _ in frontier)
                rows = await (
                    await db.execute(
                        f"""
                        SELECT id, source_id, target_id, relation_type,
                               description, source_text, evidence_span,
                               weight, round_number, layer_type,
                               confidence_score, source_agent_id
                        FROM kg_edges
                        WHERE session_id = ?
                          AND (source_id IN ({placeholders}) OR target_id IN ({placeholders}))
                        ORDER BY round_number, id
                        LIMIT 500
                        """,
                        (session_id, *frontier, *frontier),
                    )
                ).fetchall()

                next_frontier: set[str] = set()
                for row in rows:
                    edge = _edge_row(row)
                    edge_by_id[edge["id"]] = edge
                    for node_id in (edge["source_id"], edge["target_id"]):
                        if node_id not in visited:
                            visited.add(node_id)
                            next_frontier.add(node_id)
                frontier = next_frontier

            nodes = await _load_nodes(db, session_id, visited)

        return nodes, list(edge_by_id.values())

    async def paths(
        self,
        session_id: str,
        source_id: str,
        target_id: str,
        max_hops: int = 3,
    ) -> list[dict[str, Any]]:
        """Find one shortest directed-or-undirected path between two nodes."""
        if source_id == target_id:
            return [{"node_ids": [source_id], "edge_ids": [], "hops": 0, "confidence": 1.0}]

        async with get_db() as db:
            rows = await (
                await db.execute(
                    """
                    SELECT id, source_id, target_id, relation_type,
                           description, source_text, evidence_span, weight,
                           round_number,
                           layer_type, confidence_score
                    FROM kg_edges
                    WHERE session_id = ?
                    LIMIT 2000
                    """,
                    (session_id,),
                )
            ).fetchall()

        adjacency: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        for row in rows:
            edge = _edge_row(row)
            adjacency.setdefault(edge["source_id"], []).append((edge["target_id"], edge))
            adjacency.setdefault(edge["target_id"], []).append((edge["source_id"], edge))

        queue: deque[tuple[str, list[str], list[dict[str, Any]]]] = deque([(source_id, [source_id], [])])
        seen = {source_id}
        while queue:
            node_id, node_path, edge_path = queue.popleft()
            if len(edge_path) >= max(1, min(6, max_hops)):
                continue
            for next_id, edge in adjacency.get(node_id, []):
                if next_id in seen:
                    continue
                next_node_path = [*node_path, next_id]
                next_edge_path = [*edge_path, edge]
                if next_id == target_id:
                    return [
                        {
                            "node_ids": next_node_path,
                            "edge_ids": [e["id"] for e in next_edge_path],
                            "relations": [e["relation_type"] for e in next_edge_path],
                            "hops": len(next_edge_path),
                            "confidence": round(
                                sum(float(e.get("confidence", 0.5)) for e in next_edge_path)
                                / max(1, len(next_edge_path)),
                                3,
                            ),
                        }
                    ]
                seen.add(next_id)
                queue.append((next_id, next_node_path, next_edge_path))
        return []

    async def _lookup_entities(self, session_id: str, query: str, limit: int) -> list[dict[str, Any]]:
        terms = _query_terms(query)
        async with get_db() as db:
            for candidate in terms:
                term = f"%{candidate}%"
                rows = await (
                    await db.execute(
                        """
                        SELECT id, entity_type, title, description, properties,
                               layer_type, confidence_score, source_agent_id
                        FROM kg_nodes
                        WHERE session_id = ?
                          AND (title LIKE ? OR description LIKE ? OR properties LIKE ?)
                        ORDER BY confidence_score DESC, created_at DESC
                        LIMIT ?
                        """,
                        (session_id, term, term, term, limit),
                    )
                ).fetchall()
                if rows:
                    return [_node_row(row) for row in rows]
        return []

    async def _degraded_keyword_search(self, session_id: str, query: str, limit: int) -> list[dict[str, Any]]:
        term = f"%{query}%"
        async with get_db() as db:
            memory_rows = await (
                await db.execute(
                    """
                    SELECT id, agent_id, round_number, memory_text, salience_score
                    FROM agent_memories
                    WHERE session_id = ? AND memory_text LIKE ?
                    ORDER BY salience_score DESC
                    LIMIT ?
                    """,
                    (session_id, term, limit),
                )
            ).fetchall()
            action_rows = await (
                await db.execute(
                    """
                    SELECT id, agent_id, round_number, action_type, content, sentiment
                    FROM simulation_actions
                    WHERE session_id = ? AND content LIKE ?
                    ORDER BY round_number DESC, id DESC
                    LIMIT ?
                    """,
                    (session_id, term, limit),
                )
            ).fetchall()

        evidence: list[dict[str, Any]] = []
        evidence.extend(
            {
                "evidence_id": f"agent_memories:{row['id']}",
                "source": "agent_memories",
                "round_number": row["round_number"],
                "agent_id": row["agent_id"],
                "text": row["memory_text"],
                "confidence": row["salience_score"],
            }
            for row in memory_rows
        )
        evidence.extend(
            {
                "evidence_id": f"simulation_actions:{row['id']}",
                "source": "simulation_actions",
                "round_number": row["round_number"],
                "agent_id": row["agent_id"],
                "text": row["content"],
                "confidence": 0.4,
                "metadata": {"action_type": row["action_type"], "sentiment": row["sentiment"]},
            }
            for row in action_rows
        )
        return evidence[:limit]


async def _load_nodes(db: Any, session_id: str, node_ids: set[str]) -> list[dict[str, Any]]:
    if not node_ids:
        return []
    placeholders = ",".join("?" for _ in node_ids)
    rows = await (
        await db.execute(
            f"""
            SELECT id, entity_type, title, description, properties,
                   layer_type, confidence_score, source_agent_id
            FROM kg_nodes
            WHERE session_id = ? AND id IN ({placeholders})
            ORDER BY title
            """,
            (session_id, *node_ids),
        )
    ).fetchall()
    return [_node_row(row) for row in rows]


def _node_row(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "type": row["entity_type"],
        "title": row["title"],
        "description": row["description"] or "",
        "properties": row["properties"] or "{}",
        "layer_type": row["layer_type"] if "layer_type" in row.keys() else "truth",
        "confidence": float(row["confidence_score"]) if "confidence_score" in row.keys() else 1.0,
        "source_agent_id": row["source_agent_id"] if "source_agent_id" in row.keys() else None,
    }


def _edge_row(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "source_id": row["source_id"],
        "target_id": row["target_id"],
        "relation_type": row["relation_type"],
        "description": row["description"] or "",
        "source_text": row["source_text"] if "source_text" in row.keys() else None,
        "evidence_span": row["evidence_span"] if "evidence_span" in row.keys() else None,
        "weight": float(row["weight"] or 1.0),
        "round_number": row["round_number"] if "round_number" in row.keys() else 0,
        "layer_type": row["layer_type"] if "layer_type" in row.keys() else "truth",
        "confidence": float(row["confidence_score"]) if "confidence_score" in row.keys() else 1.0,
        "source_agent_id": row["source_agent_id"] if "source_agent_id" in row.keys() else None,
    }


def _edge_to_evidence(edge: dict[str, Any]) -> dict[str, Any] | None:
    text = edge.get("source_text") or edge.get("description")
    if not text and not edge.get("evidence_span"):
        return None
    return {
        "evidence_id": f"kg_edges:{edge['id']}",
        "source": "kg_edges",
        "edge_id": edge["id"],
        "round_number": edge.get("round_number", 0),
        "text": text,
        "evidence_span": edge.get("evidence_span"),
        "confidence": edge.get("confidence", edge.get("weight", 0.5)),
    }


def _confidence(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    matched_nodes: list[dict[str, Any]],
) -> float:
    if not nodes:
        return 0.0
    node_score = sum(float(n.get("confidence", 0.5)) for n in matched_nodes) / max(1, len(matched_nodes))
    edge_score = sum(float(e.get("confidence", 0.5)) for e in edges) / max(1, len(edges)) if edges else 0.35
    structure_bonus = min(0.15, len(edges) * 0.02)
    return round(max(0.0, min(1.0, (node_score * 0.55) + (edge_score * 0.3) + structure_bonus)), 3)


def _query_terms(query: str) -> list[str]:
    clean = query.strip()
    terms = [clean]
    terms.extend(part for part in clean.replace("?", " ").replace("？", " ").split() if len(part) >= 2)
    if len(clean) >= 3:
        terms.append(clean[:3])
    if len(clean) >= 2:
        terms.append(clean[:2])
    deduped: list[str] = []
    seen = set()
    for term in terms:
        if term and term not in seen:
            deduped.append(term)
            seen.add(term)
    return deduped

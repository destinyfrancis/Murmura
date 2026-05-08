"""Deterministic grounded prediction report builder.

This is a no-LLM report spine used for Stage 8 parity: it assembles standard
forecast sections from persisted simulation data and GraphRAG evidence, while
clearly separating observed simulation results from forecast judgement.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from backend.app.services.graph_rag_query import GraphRAGQueryService
from backend.app.utils.db import get_db


@dataclass(frozen=True)
class GroundedReportBundle:
    """Structured report bundle with markdown and evidence appendix."""

    report_id: str
    title: str
    content_markdown: str
    summary: str
    key_findings: tuple[str, ...]
    evidence_bundle: tuple[dict[str, Any], ...]

    def to_report_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "title": self.title,
            "content_markdown": self.content_markdown,
            "summary": self.summary,
            "key_findings": list(self.key_findings),
            "charts_data": {"evidence_bundle": list(self.evidence_bundle)},
            "agent_log": [],
            "total_cost_usd": 0.0,
        }


class GroundedReportBuilder:
    """Build a standard evidence-linked report from local DB state."""

    async def build(
        self,
        session_id: str,
        report_mode: str = "social_forecast",
        question: str | None = None,
    ) -> GroundedReportBundle:
        session = await self._load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        mode = _normalise_report_mode(report_mode, session.get("scenario_type", ""))
        query = (question or session.get("scenario_question") or session.get("seed_text") or mode).strip()
        graph_session_id = session.get("graph_id") or session_id
        graph_result = await GraphRAGQueryService().query(graph_session_id, query[:120], hops=2, limit=12, strict=False)
        action_summary = await self._load_action_summary(session_id)
        hidden_actors = await self._load_hidden_actors(graph_session_id)
        faction_summary = await self._load_faction_summary(session_id)
        graph_summary = await self._load_graph_summary(graph_session_id)

        evidence = tuple(graph_result.evidence)
        findings = _findings(mode, action_summary, hidden_actors, graph_result.confidence, graph_summary)
        markdown = _render_markdown(
            session=session,
            mode=mode,
            query=query,
            findings=findings,
            action_summary=action_summary,
            hidden_actors=hidden_actors,
            faction_summary=faction_summary,
            graph_summary=graph_summary,
            graph_data=graph_result.to_dict(),
            evidence=evidence,
        )

        return GroundedReportBundle(
            report_id=str(uuid4()),
            title=_title_for_mode(mode),
            content_markdown=markdown,
            summary=findings[0] if findings else "Grounded simulation report generated.",
            key_findings=tuple(findings),
            evidence_bundle=evidence,
        )

    async def _load_session(self, session_id: str) -> dict[str, Any] | None:
        async with get_db() as db:
            row = await (
                await db.execute(
                    """
                    SELECT id, name, sim_mode, seed_text, scenario_type, graph_id,
                           scenario_question, status, current_round, round_count
                    FROM simulation_sessions
                    WHERE id = ?
                    """,
                    (session_id,),
                )
            ).fetchone()
        return dict(row) if row else None

    async def _load_action_summary(self, session_id: str) -> dict[str, Any]:
        async with get_db() as db:
            total_row = await (
                await db.execute(
                    """
                    SELECT COUNT(*) AS total,
                           SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) AS positive,
                           SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) AS negative,
                           SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) AS neutral,
                           MAX(round_number) AS latest_round
                    FROM simulation_actions
                    WHERE session_id = ?
                    """,
                    (session_id,),
                )
            ).fetchone()
            platform_rows = await (
                await db.execute(
                    """
                    SELECT platform, COUNT(*) AS count
                    FROM simulation_actions
                    WHERE session_id = ?
                    GROUP BY platform
                    ORDER BY count DESC
                    """,
                    (session_id,),
                )
            ).fetchall()
            top_actions = await (
                await db.execute(
                    """
                    SELECT round_number, oasis_username, action_type,
                           platform, content, sentiment
                    FROM simulation_actions
                    WHERE session_id = ? AND content != ''
                    ORDER BY round_number DESC, id DESC
                    LIMIT 8
                    """,
                    (session_id,),
                )
            ).fetchall()
        return {
            "total_actions": int(total_row["total"] or 0),
            "positive": int(total_row["positive"] or 0),
            "negative": int(total_row["negative"] or 0),
            "neutral": int(total_row["neutral"] or 0),
            "latest_round": int(total_row["latest_round"] or 0),
            "platforms": [dict(r) for r in platform_rows],
            "recent_actions": [dict(r) for r in top_actions],
        }

    async def _load_hidden_actors(self, session_id: str) -> list[dict[str, Any]]:
        async with get_db() as db:
            rows = await (
                await db.execute(
                    """
                    SELECT id, title, entity_type, description, properties,
                           confidence_score
                    FROM kg_nodes
                    WHERE session_id = ? AND properties LIKE '%implicit_discovery%'
                    ORDER BY confidence_score DESC
                    LIMIT 12
                    """,
                    (session_id,),
                )
            ).fetchall()
        actors = []
        for row in rows:
            props = json.loads(row["properties"] or "{}")
            if props.get("actor_node_id"):
                continue
            actors.append(
                {
                    "id": row["id"],
                    "name": row["title"],
                    "entity_type": row["entity_type"],
                    "role": row["description"] or props.get("inferred_role", ""),
                    "evidence_phrase": props.get("evidence_phrase", ""),
                    "confidence": row["confidence_score"],
                    "include_in_simulation": props.get("include_in_simulation", True),
                }
            )
        return actors

    async def _load_faction_summary(self, session_id: str) -> list[dict[str, Any]]:
        async with get_db() as db:
            rows = await (
                await db.execute(
                    """
                    SELECT round_number, cluster_id, core_narrative,
                           shared_anxieties, member_count
                    FROM community_summaries
                    WHERE session_id = ?
                    ORDER BY round_number DESC, member_count DESC
                    LIMIT 6
                    """,
                    (session_id,),
                )
            ).fetchall()
        return [dict(r) for r in rows]

    async def _load_graph_summary(self, graph_session_id: str) -> dict[str, Any]:
        async with get_db() as db:
            node_count_row = await (
                await db.execute("SELECT COUNT(*) AS count FROM kg_nodes WHERE session_id = ?", (graph_session_id,))
            ).fetchone()
            edge_count_row = await (
                await db.execute("SELECT COUNT(*) AS count FROM kg_edges WHERE session_id = ?", (graph_session_id,))
            ).fetchone()
            relation_rows = await (
                await db.execute(
                    """
                    SELECT relation_type, COUNT(*) AS count
                    FROM kg_edges
                    WHERE session_id = ?
                    GROUP BY relation_type
                    ORDER BY count DESC, relation_type
                    LIMIT 8
                    """,
                    (graph_session_id,),
                )
            ).fetchall()
            node_rows = await (
                await db.execute(
                    """
                    SELECT title, entity_type, description, confidence_score
                    FROM kg_nodes
                    WHERE session_id = ?
                    ORDER BY confidence_score DESC, title
                    LIMIT 12
                    """,
                    (graph_session_id,),
                )
            ).fetchall()
        return {
            "graph_session_id": graph_session_id,
            "node_count": int(node_count_row["count"] or 0) if node_count_row else 0,
            "edge_count": int(edge_count_row["count"] or 0) if edge_count_row else 0,
            "top_relations": [dict(r) for r in relation_rows],
            "top_nodes": [dict(r) for r in node_rows],
        }


def _normalise_report_mode(report_mode: str, scenario_type: str) -> str:
    requested = (report_mode or "").lower()
    if requested in {"social_forecast", "relationship_forecast", "market_launch_forecast"}:
        return requested
    if scenario_type in {"relationship", "family", "workplace"}:
        return "relationship_forecast"
    if scenario_type in {"market", "b2b", "company_competitor", "product_launch"}:
        return "market_launch_forecast"
    return "social_forecast"


def _title_for_mode(mode: str) -> str:
    return {
        "social_forecast": "Social Forecast Report",
        "relationship_forecast": "Relationship Forecast Report",
        "market_launch_forecast": "Market Launch Forecast Report",
    }.get(mode, "Grounded Forecast Report")


def _findings(
    mode: str,
    action_summary: dict[str, Any],
    hidden_actors: list[dict[str, Any]],
    graph_confidence: float,
    graph_summary: dict[str, Any],
) -> list[str]:
    total = action_summary["total_actions"]
    if total == 0:
        return [
            "No logged simulation actions were available, so this report is a graph-based scenario forecast rather than an observed social-response report.",
            (
                f"The knowledge graph contains {graph_summary['node_count']} nodes and "
                f"{graph_summary['edge_count']} edges; use it as the primary evidence layer."
            ),
            f"{len(hidden_actors)} evidence-linked hidden actors remain important uncertainty checks.",
            f"GraphRAG retrieval confidence is {graph_confidence:.2f}; claims below cite evidence where available.",
        ]

    neg = action_summary["negative"]
    pos = action_summary["positive"]
    sentiment = "mixed"
    if total and neg / total >= 0.45:
        sentiment = "negative-skewed"
    elif total and pos / total >= 0.45:
        sentiment = "positive-skewed"

    mode_claim = {
        "social_forecast": "Observed social response should be treated as a propagation signal, not a final outcome.",
        "relationship_forecast": (
            "Observed interactions indicate relationship pressure points rather than fixed intent."
        ),
        "market_launch_forecast": "Observed reactions are early adoption and narrative signals, not sales certainty.",
    }[mode]
    return [
        f"{mode_claim} Current action sentiment is {sentiment} across {total} logged actions.",
        f"{len(hidden_actors)} evidence-linked hidden actors remain important uncertainty checks.",
        f"GraphRAG retrieval confidence is {graph_confidence:.2f}; claims below cite evidence where available.",
    ]


def _render_markdown(
    session: dict[str, Any],
    mode: str,
    query: str,
    findings: list[str],
    action_summary: dict[str, Any],
    hidden_actors: list[dict[str, Any]],
    faction_summary: list[dict[str, Any]],
    graph_summary: dict[str, Any],
    graph_data: dict[str, Any],
    evidence: tuple[dict[str, Any], ...],
) -> str:
    evidence_ids = [e["evidence_id"] for e in evidence[:8]]
    has_actions = action_summary["total_actions"] > 0
    recent_actions = "\n".join(
        f"- R{a['round_number']} {a['oasis_username']} [{a['platform']}]: {a['content'][:140]}"
        for a in action_summary["recent_actions"]
    ) or "- No OASIS action timeline was produced; this section is intentionally empty."
    hidden_text = "\n".join(
        f"- {a['name']} ({a['entity_type']}, confidence={float(a['confidence'] or 0):.2f}): {a['evidence_phrase']}"
        for a in hidden_actors
    ) or "- No evidence-linked hidden actors recorded."
    faction_text = "\n".join(
        f"- R{f['round_number']} cluster {f['cluster_id']} ({f['member_count']} agents): {f['core_narrative']}"
        for f in faction_summary
    ) or "- No faction summary has been generated yet."
    evidence_text = "\n".join(
        f"- {e['evidence_id']}: {str(e.get('text', ''))[:160]}"
        for e in evidence[:12]
    ) or "- No graph evidence matched; retrieval mode may be degraded."
    graph_nodes = "\n".join(
        f"- {n['title']} ({n['entity_type']}, confidence={float(n['confidence_score'] or 0):.2f})"
        for n in graph_summary["top_nodes"][:8]
    ) or "- No graph nodes recorded."
    graph_relations = "\n".join(
        f"- {r['relation_type']}: {r['count']}"
        for r in graph_summary["top_relations"][:6]
    ) or "- No graph relations recorded."

    sections = _mode_sections(mode)
    forecast = _scenario_forecast_sections(mode, has_actions)
    return f"""# {_title_for_mode(mode)}

## Executive Verdict
{findings[0]}

Major claim evidence: {", ".join(evidence_ids) if evidence_ids else "no graph evidence id available"}.

## Forecast Timeline
{forecast['timeline']}

## Stakeholder Reactions
{recent_actions}

## Scenario Outcome Matrix
{forecast['outcomes']}

## Graph Structure
- Nodes: {graph_summary['node_count']}
- Edges: {graph_summary['edge_count']}

Top actors and objects:
{graph_nodes}

Top relation types:
{graph_relations}

## Hidden Actors
{hidden_text}

## Faction Map
{faction_text}

## Key Uncertainties
- Graph retrieval mode: `{graph_data['mode']}` with confidence {graph_data['confidence']}.
- Observation/forecast boundary: logged posts/actions are observed simulation results;
  recommendations are forecast judgement.
- Query framing: {query[:240]}

## Early Warning Indicators
{forecast['signals']}

## What-if Interventions
{sections['interventions']}

## Recommended Actions
{sections['actions']}

## Evidence Appendix
{evidence_text}
"""


def _scenario_forecast_sections(mode: str, has_actions: bool) -> dict[str, str]:
    if has_actions:
        return {
            "timeline": (
                "- Near term: watch whether the dominant sentiment pattern persists beyond the latest logged round.\n"
                "- Mid term: compare new belief-layer KG edges against seed-truth edges before treating the trend as stable.\n"
                "- Long term: rerun what-if branches for any intervention that changes hidden actor incentives."
            ),
            "outcomes": (
                "- Continuity path: current simulated response persists with limited structural change.\n"
                "- Narrative shift path: a visible stakeholder reframes the issue and changes adoption/escalation pressure.\n"
                "- Shock path: an external intervention changes constraints faster than agents can adapt."
            ),
            "signals": (
                "- Sudden concentration of negative actions around one actor or topic.\n"
                "- New high-confidence KG edges that connect previously separate factions.\n"
                "- Divergence between belief states and observed action sentiment."
            ),
        }
    if mode == "market_launch_forecast":
        return {
            "timeline": (
                "- Near term: validate whether demand, trust, and regulator nodes are central in the graph.\n"
                "- Mid term: stress-test competitor, reviewer, and compliance responses before treating launch readiness as stable.\n"
                "- Long term: rerun with action-producing simulation once OASIS is available."
            ),
            "outcomes": (
                "- Controlled adoption: early users respond positively while operational constraints stay manageable.\n"
                "- Narrative drag: trust or product-claim concerns slow conversion despite visible interest.\n"
                "- Competitive counter-move: rivals or substitutes redirect attention and compress pricing power.\n"
                "- Compliance shock: regulator or platform constraints force message/product changes."
            ),
            "signals": (
                "- Regulator, reviewer, or customer-support nodes gaining more KG edges.\n"
                "- Evidence phrases linking product claims to distrust, safety, or cost.\n"
                "- Competitor nodes becoming bridges between customer and media nodes."
            ),
        }
    if mode == "relationship_forecast":
        return {
            "timeline": (
                "- Near term: identify which trust, pressure, or third-party nodes dominate the graph.\n"
                "- Mid term: test mediation, timing, and communication-tone interventions.\n"
                "- Long term: rerun with action-producing simulation once OASIS is available."
            ),
            "outcomes": (
                "- Repair path: explicit clarification lowers uncertainty and restores trust.\n"
                "- Avoidance path: unresolved pressure produces distance without open rupture.\n"
                "- Escalation path: a third-party or repeated trigger amplifies mistrust.\n"
                "- Boundary reset: actors preserve stability by reducing contact or renegotiating roles."
            ),
            "signals": (
                "- Nodes describing trust, betrayal, obligation, or reputation becoming central.\n"
                "- Evidence linking one actor to repeated unresolved pressure.\n"
                "- New graph edges connecting private conflict to public or group-level consequences."
            ),
        }
    return {
        "timeline": (
            "- Near term: monitor whether central actors move toward restraint, signalling, or escalation.\n"
            "- Mid term: stress-test mediator, proxy, economic, and logistics nodes as branching points.\n"
            "- Long term: rerun with action-producing simulation once OASIS is available."
        ),
        "outcomes": (
            "- De-escalation/framework path: mediators or cost constraints create space for a limited agreement.\n"
            "- Contained escalation path: direct actors exchange signals or limited strikes while avoiding full mobilisation.\n"
            "- Protracted low-intensity path: proxy, media, or economic actors sustain pressure below open-war threshold.\n"
            "- Systemic shock path: trade, energy, finance, or logistics nodes transmit the conflict outward.\n"
            "- Regional-war path: a direct military boundary crossing or major retaliation synchronises multiple fronts."
        ),
        "signals": (
            "- Military or proxy nodes becoming bridges between state actors and civilian/economic nodes.\n"
            "- Shipping, insurance, energy, sanctions, or market nodes gaining high-confidence edges.\n"
            "- Mediator nodes disappearing from the strongest paths, or retaliation nodes becoming central.\n"
            "- Evidence of domestic mobilisation, legal authorisation, or alliance activation."
        ),
    }


def _mode_sections(mode: str) -> dict[str, str]:
    if mode == "relationship_forecast":
        return {
            "interventions": "- Test repair timing, third-party mediation, and communication tone changes.",
            "actions": (
                "- Prioritise trust repair, clarify assumptions, and track attachment/trust shifts round by round."
            ),
        }
    if mode == "market_launch_forecast":
        return {
            "interventions": (
                "- Test pricing, reviewer/influencer response, competitor counter-moves, and regulator messaging."
            ),
            "actions": (
                "- Reduce adoption blockers, prepare competitor response playbooks, and cite evidence in launch claims."
            ),
        }
    return {
        "interventions": (
            "- Test moderation, public explanation timing, trusted messenger choices, and de-escalation shocks."
        ),
        "actions": (
            "- Monitor propagation, polarisation, trust drift, and hidden actor incentives before escalation decisions."
        ),
    }

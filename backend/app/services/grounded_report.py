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
        graph_result = await GraphRAGQueryService().query(session_id, query[:120], hops=2, limit=12, strict=False)
        action_summary = await self._load_action_summary(session_id)
        hidden_actors = await self._load_hidden_actors(session_id)
        faction_summary = await self._load_faction_summary(session_id)

        evidence = tuple(graph_result.evidence)
        findings = _findings(mode, action_summary, hidden_actors, graph_result.confidence)
        markdown = _render_markdown(
            session=session,
            mode=mode,
            query=query,
            findings=findings,
            action_summary=action_summary,
            hidden_actors=hidden_actors,
            faction_summary=faction_summary,
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
                    SELECT id, name, sim_mode, seed_text, scenario_type,
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
) -> list[str]:
    total = action_summary["total_actions"]
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
    graph_data: dict[str, Any],
    evidence: tuple[dict[str, Any], ...],
) -> str:
    evidence_ids = [e["evidence_id"] for e in evidence[:8]]
    recent_actions = "\n".join(
        f"- R{a['round_number']} {a['oasis_username']} [{a['platform']}]: {a['content'][:140]}"
        for a in action_summary["recent_actions"]
    ) or "- No logged actions yet."
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

    sections = _mode_sections(mode)
    return f"""# {_title_for_mode(mode)}

## Executive Verdict
{findings[0]}

Major claim evidence: {", ".join(evidence_ids) if evidence_ids else "no graph evidence id available"}.

## Forecast Timeline
- Near term: watch whether the dominant sentiment pattern persists beyond round {action_summary['latest_round']}.
- Mid term: compare new belief-layer KG edges against seed-truth edges before treating the trend as stable.
- Long term: rerun what-if branches for any intervention that changes hidden actor incentives.

## Stakeholder Reactions
{recent_actions}

## Hidden Actors
{hidden_text}

## Faction Map
{faction_text}

## Key Uncertainties
- Graph retrieval mode: `{graph_data['mode']}` with confidence {graph_data['confidence']}.
- Observation/forecast boundary: logged posts/actions are observed simulation results;
  recommendations are forecast judgement.
- Query framing: {query[:240]}

## What-if Interventions
{sections['interventions']}

## Recommended Actions
{sections['actions']}

## Evidence Appendix
{evidence_text}
"""


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

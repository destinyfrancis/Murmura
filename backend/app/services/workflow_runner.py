"""Asynchronous one-click workflow runner.

The legacy quick-start endpoint performed graph build, agent generation, and
simulation startup inside one HTTP request. This service records a durable
workflow row, emits progress events, and lets the frontend render a live graph
while backend steps continue independently.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.app.models.simulation_config import resolve_preset
from backend.app.services.graph_builder import GraphBuilderService
from backend.app.services.simulation_manager import (
    generate_agents,
    get_simulation_manager,
    store_universal_agent_profiles,
    store_universal_agent_relationships,
)
from backend.app.services.zero_config import ZeroConfigService
from backend.app.utils.db import get_db
from backend.app.utils.logger import get_logger
from backend.app.utils.prompt_security import sanitize_scenario_description, sanitize_source_seed_text

logger = get_logger(__name__)


_TOTAL_STEPS = 5


class WorkflowRunner:
    """Run a seed-to-report workflow and persist progress events."""

    async def create_workflow(
        self,
        *,
        seed_text: str,
        scenario_question: str = "",
        preset: str = "fast",
        owner_id: str | None = None,
    ) -> dict[str, Any]:
        await self._ensure_schema()
        workflow_id = str(uuid.uuid4())
        safe_seed = sanitize_source_seed_text(seed_text)
        safe_question = sanitize_scenario_description(scenario_question) if scenario_question else ""
        now = _utc_now()

        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO workflow_runs
                    (id, status, current_step, step_index, total_steps, message,
                     seed_text, scenario_question, preset, owner_id, created_at, updated_at)
                VALUES (?, 'queued', 'queued', 0, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow_id,
                    _TOTAL_STEPS,
                    "Workflow queued",
                    safe_seed,
                    safe_question,
                    preset,
                    owner_id,
                    now,
                    now,
                ),
            )
            await db.commit()

        await self._event(
            workflow_id,
            "queued",
            "queued",
            "Workflow queued",
            {"preset": preset, "seed_chars": len(safe_seed)},
        )
        return {"workflow_id": workflow_id, "status": "queued"}

    async def run(self, workflow_id: str) -> None:
        await self._ensure_schema()
        row = await self._load_run(workflow_id)
        if not row:
            logger.warning("Workflow %s not found", workflow_id)
            return

        seed_text = row["seed_text"]
        scenario_question = row["scenario_question"] or ""
        preset = row["preset"] or "fast"
        owner_id = row["owner_id"]

        try:
            await self._update(workflow_id, status="running", step="graph", step_index=1, message="Building graph")

            zc = ZeroConfigService()
            config = await zc.prepare(seed_text)
            resolved = resolve_preset(preset)
            await self._event(
                workflow_id,
                "mode_detected",
                "graph",
                "Scenario mode detected",
                {
                    "mode": config.mode,
                    "domain_pack_id": config.domain_pack_id,
                    "agent_count": resolved.agents,
                    "round_count": resolved.rounds,
                },
            )

            graph_seed_id = str(uuid.uuid4())
            graph_builder = GraphBuilderService()
            try:
                graph_result = await asyncio.wait_for(
                    graph_builder.build_graph_from_seed(
                        graph_id=graph_seed_id,
                        scenario_type=config.domain_pack_id,
                        seed_text=seed_text,
                    ),
                    timeout=90,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Graph build degraded for workflow %s: %s", workflow_id, exc)
                graph_result = await self._build_fallback_graph(
                    graph_builder=graph_builder,
                    graph_id=graph_seed_id,
                    scenario_type=config.domain_pack_id,
                    seed_text=seed_text,
                )
            graph_id = graph_result.get("graph_id") or graph_seed_id
            node_count = int(graph_result.get("node_count") or 0)
            edge_count = int(graph_result.get("edge_count") or 0)
            await self._update(
                workflow_id,
                step="env",
                step_index=2,
                message="Graph ready; generating agents",
                graph_id=graph_id,
                artifacts={"node_count": node_count, "edge_count": edge_count},
            )
            await self._event(
                workflow_id,
                "graph_built",
                "graph",
                "Knowledge graph built",
                {"graph_id": graph_id, "node_count": node_count, "edge_count": edge_count},
            )

            time_config = await zc.infer_time_config(seed_text, resolved.rounds)
            manager = get_simulation_manager()
            is_kg = config.mode == "kg_driven"
            session_data = await manager.create_session(
                {
                    "name": f"Workflow: {seed_text[:50]}",
                    "scenario_type": "kg_driven" if is_kg else "property",
                    "seed_text": seed_text,
                    "agent_count": resolved.agents,
                    "round_count": resolved.rounds,
                    "graph_id": graph_id,
                    "domain_pack_id": config.domain_pack_id,
                    "platforms": {"twitter": True, "reddit": True},
                    "time_config": time_config.to_dict(),
                    "owner_id": owner_id,
                },
                csv_path=None,
            )
            session_id = session_data["session_id"]
            await self._update(workflow_id, session_id=session_id)
            await self._event(
                workflow_id,
                "session_created",
                "env",
                "Simulation session created",
                {"session_id": session_id, "agent_count": resolved.agents, "round_count": resolved.rounds},
            )

            if is_kg:
                profiles, csv_path = await generate_agents(
                    session_id=session_id,
                    request={"graph_id": graph_id, "seed_text": seed_text, "agent_count": resolved.agents},
                    mode="kg_driven",
                )
                try:
                    await store_universal_agent_profiles(session_id, profiles)
                except Exception:  # noqa: BLE001
                    logger.warning(
                        "Could not store universal agent profiles for workflow session %s",
                        session_id,
                        exc_info=True,
                    )
                try:
                    await store_universal_agent_relationships(session_id, profiles)
                except Exception:  # noqa: BLE001
                    logger.warning(
                        "Could not store universal agent relationships for workflow session %s",
                        session_id,
                        exc_info=True,
                    )
                agent_names = [getattr(profile, "name", "") for profile in profiles[:30]]
            else:
                profiles, csv_path = await generate_agents(
                    session_id=session_id,
                    request={
                        "agent_count": resolved.agents,
                        "scenario_type": "property",
                        "domain_pack_id": config.domain_pack_id,
                    },
                    mode="hk_demographic",
                )
                agent_names = [f"Agent {idx}" for idx in range(1, min(len(profiles), 30) + 1)]

            await self._event(
                workflow_id,
                "agents_generated",
                "env",
                "Agent cast generated",
                {"agent_count": len(profiles), "agents": agent_names, "csv_path": csv_path},
            )

            from backend.app.services.oasis_compatibility import get_capabilities  # noqa: PLC0415

            capabilities = get_capabilities()
            simulation_available = bool(capabilities.get("simulation_available", capabilities.get("simulation")))
            simulation_skipped = not simulation_available
            if simulation_available:
                await self._update(workflow_id, step="simulation", step_index=3, message="Simulation queued")
                await manager.start_session(session_id)
                await self._event(
                    workflow_id,
                    "simulation_started",
                    "simulation",
                    "Simulation queued",
                    {"session_id": session_id},
                )
                await self._monitor_simulation(workflow_id, session_id)
            else:
                reason = str(capabilities.get("reason") or "unknown")
                await self._update(
                    workflow_id,
                    step="report",
                    step_index=4,
                    message="Simulation engine unavailable; generating graph forecast",
                    artifacts={"simulation_skipped": True, "simulation_skip_reason": reason},
                )
                await self._event(
                    workflow_id,
                    "simulation_skipped",
                    "simulation",
                    "Simulation engine unavailable; graph forecast mode active",
                    {"session_id": session_id, "reason": reason},
                )

            await self._update(workflow_id, step="report", step_index=4, message="Generating report")
            try:
                from backend.app.services.report_agent import ReportAgent  # noqa: PLC0415

                report = await ReportAgent().generate_report(
                    session_id=session_id,
                    report_type="grounded",
                    scenario_question=scenario_question,
                )
                report_id = report.get("report_id")
                await self._update(workflow_id, report_id=report_id)
                await self._event(
                    workflow_id,
                    "report_generated",
                    "report",
                    "Report generated",
                    {"report_id": report_id},
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Workflow report generation failed for %s: %s", workflow_id, exc)
                await self._event(
                    workflow_id,
                    "report_degraded",
                    "report",
                    "Report generation degraded; simulation artifacts are available",
                    {"error": exc.__class__.__name__},
                )

            await self._update(
                workflow_id,
                status="degraded" if simulation_skipped else "completed",
                step="interaction",
                step_index=5,
                message=(
                    "Workflow completed with graph forecast fallback"
                    if simulation_skipped
                    else "Workflow completed"
                ),
            )
            await self._event(
                workflow_id,
                "degraded" if simulation_skipped else "completed",
                "interaction",
                (
                    "Workflow completed with graph forecast fallback"
                    if simulation_skipped
                    else "Workflow completed"
                ),
                {},
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Workflow %s failed", workflow_id)
            await self._update(
                workflow_id,
                status="failed",
                message="Workflow failed",
                error_message=str(exc.__class__.__name__),
            )
            await self._event(
                workflow_id,
                "failed",
                "error",
                "Workflow failed",
                {"error": exc.__class__.__name__},
            )

    async def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        await self._ensure_schema()
        row = await self._load_run(workflow_id)
        if not row:
            return None

        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT event_type, step, message, payload_json, created_at
                FROM workflow_events
                WHERE workflow_id = ?
                ORDER BY id ASC
                """,
                (workflow_id,),
            )
            events = [dict(r) for r in await cursor.fetchall()]

        for event in events:
            event["payload"] = json.loads(event.pop("payload_json") or "{}")
        data = dict(row)
        data["artifacts"] = json.loads(data.pop("artifacts_json") or "{}")
        data["events"] = events
        return data

    async def _monitor_simulation(self, workflow_id: str, session_id: str) -> None:
        manager = get_simulation_manager()
        last_status = ""
        for _ in range(240):
            session = await manager.get_session(session_id)
            status = str(session.get("status") or "")
            current_round = int(session.get("current_round") or 0)
            total_rounds = int(session.get("round_count") or 0)
            if status != last_status or current_round:
                await self._event(
                    workflow_id,
                    "simulation_status",
                    "simulation",
                    f"Simulation {status or 'pending'}",
                    {"status": status, "current_round": current_round, "total_rounds": total_rounds},
                )
                last_status = status
            if status in {"completed", "failed"}:
                if status == "failed":
                    raise RuntimeError("simulation_failed")
                return
            await asyncio.sleep(2)
        raise TimeoutError("simulation monitor timed out")

    async def _build_fallback_graph(
        self,
        *,
        graph_builder: GraphBuilderService,
        graph_id: str,
        scenario_type: str,
        seed_text: str,
    ) -> dict[str, Any]:
        """Create a small evidence graph so agent generation can continue."""
        await graph_builder._ensure_graph_session(graph_id, scenario_type, seed_text)  # noqa: SLF001
        actor_specs = _fallback_actor_specs(seed_text)
        node_rows = [
            (
                f"{graph_id[:8]}_fallback_{idx}",
                graph_id,
                entity_type,
                title,
                description,
                json.dumps({"source": "workflow_fallback", "include_in_simulation": True}, ensure_ascii=False),
                0.35,
            )
            for idx, (entity_type, title, description) in enumerate(actor_specs, start=1)
        ]
        edge_rows = []
        for idx in range(len(node_rows) - 1):
            edge_rows.append(
                (
                    graph_id,
                    node_rows[idx][0],
                    node_rows[idx + 1][0],
                    "influences",
                    "Fallback relation inferred from seed co-occurrence when LLM graph build was unavailable.",
                    seed_text[:500],
                    0.25,
                    0.35,
                )
            )
        async with get_db() as db:
            await db.executemany(
                """
                INSERT OR REPLACE INTO kg_nodes
                    (id, session_id, entity_type, title, description, properties, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                node_rows,
            )
            await db.executemany(
                """
                INSERT INTO kg_edges
                    (session_id, source_id, target_id, relation_type, description,
                     source_text, weight, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                edge_rows,
            )
            await db.commit()
        return {
            "graph_id": graph_id,
            "session_id": graph_id,
            "node_count": len(node_rows),
            "edge_count": len(edge_rows),
            "entity_types": sorted({row[2] for row in node_rows}),
            "relation_types": ["influences"],
            "scenario_type": scenario_type,
            "fallback_graph": True,
        }

    async def _ensure_schema(self) -> None:
        async with get_db() as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    current_step TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    total_steps INTEGER NOT NULL,
                    message TEXT NOT NULL DEFAULT '',
                    seed_text TEXT NOT NULL,
                    scenario_question TEXT DEFAULT '',
                    preset TEXT DEFAULT 'fast',
                    owner_id TEXT,
                    graph_id TEXT,
                    session_id TEXT,
                    report_id TEXT,
                    error_message TEXT,
                    artifacts_json TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    step TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload_json TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(workflow_id) REFERENCES workflow_runs(id) ON DELETE CASCADE
                )
                """
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_workflow_events_run ON workflow_events(workflow_id, id)"
            )
            await db.commit()

    async def _load_run(self, workflow_id: str) -> Any | None:
        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM workflow_runs WHERE id = ?", (workflow_id,))
            return await cursor.fetchone()

    async def _update(
        self,
        workflow_id: str,
        *,
        status: str | None = None,
        step: str | None = None,
        step_index: int | None = None,
        message: str | None = None,
        graph_id: str | None = None,
        session_id: str | None = None,
        report_id: str | None = None,
        error_message: str | None = None,
        artifacts: dict[str, Any] | None = None,
    ) -> None:
        current = await self._load_run(workflow_id)
        current_artifacts = json.loads(current["artifacts_json"] or "{}") if current else {}
        if artifacts:
            current_artifacts.update(artifacts)
        updates = {
            "status": status,
            "current_step": step,
            "step_index": step_index,
            "message": message,
            "graph_id": graph_id,
            "session_id": session_id,
            "report_id": report_id,
            "error_message": error_message,
            "artifacts_json": json.dumps(current_artifacts, ensure_ascii=False),
            "updated_at": _utc_now(),
        }
        assignments = []
        values: list[Any] = []
        for key, value in updates.items():
            if value is not None:
                assignments.append(f"{key} = ?")
                values.append(value)
        if not assignments:
            return
        values.append(workflow_id)
        async with get_db() as db:
            await db.execute(
                f"UPDATE workflow_runs SET {', '.join(assignments)} WHERE id = ?",
                values,
            )
            await db.commit()

    async def _event(
        self,
        workflow_id: str,
        event_type: str,
        step: str,
        message: str,
        payload: dict[str, Any],
    ) -> None:
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO workflow_events
                    (workflow_id, event_type, step, message, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow_id,
                    event_type,
                    step,
                    message,
                    json.dumps(payload, ensure_ascii=False),
                    _utc_now(),
                ),
            )
            await db.commit()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fallback_actor_specs(seed_text: str) -> list[tuple[str, str, str]]:
    text = seed_text.lower()
    specs: list[tuple[str, str, str]] = []
    if "iran" in text or "伊朗" in seed_text:
        specs.extend(
            [
                ("Country", "Iran", "State actor balancing deterrence, regime legitimacy, and economic pressure."),
                ("Government", "Iranian leadership", "Decision-making circle around escalation, negotiation, and domestic consent."),
            ]
        )
    if "united states" in text or "u.s." in text or " us " in f" {text} " or "美國" in seed_text:
        specs.extend(
            [
                ("Country", "United States", "State actor balancing coercive diplomacy, alliance commitments, and domestic politics."),
                ("Government", "US administration", "Executive decision-makers shaping sanctions, force posture, and negotiation terms."),
            ]
        )
    if "israel" in text or "以色列" in seed_text:
        specs.append(("Country", "Israel", "Regional state actor affected by deterrence, threat perception, and alliance signals."))
    if "oil" in text or "荷爾木茲" in seed_text or "hormuz" in text:
        specs.append(("EconomicActor", "Energy and shipping markets", "Market actor repricing supply disruption, insurance, and transport risk."))
    specs.extend(
        [
            ("InternationalOrganization", "International mediators", "Diplomatic actors attempting to reduce escalation and preserve channels."),
            ("MediaOutlet", "Global media ecosystem", "Narrative actor amplifying casualty claims, threats, leaks, and public opinion frames."),
            ("CivilSociety", "Regional civilians and diaspora publics", "Non-state public actor reacting to insecurity, nationalism, and humanitarian costs."),
            ("NonStateActor", "Regional armed non-state actors", "Proxy or aligned armed groups able to alter escalation dynamics."),
        ]
    )
    deduped: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for spec in specs:
        if spec[1] not in seen:
            seen.add(spec[1])
            deduped.append(spec)
    return deduped[:18]

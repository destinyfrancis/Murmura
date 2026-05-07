"""KG-driven universal agent factory.

Converts knowledge graph nodes and edges into UniversalAgentProfile instances
via a two-stage LLM pipeline:

  Stage 1 — Eligibility filter: determine which KG nodes are concrete actors
  Stage 2 — Profile generation: generate full agent profiles from eligible nodes

This service makes the simulation engine domain-agnostic: any scenario that can
be described as a knowledge graph (geopolitical, corporate, historical, etc.)
can be converted into OASIS-compatible simulation agents.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import replace as dc_replace
from typing import Any

from backend.app.models.platform_identity import (
    PlatformIdentity,
    PlatformType,
    build_platform_identity,
)
from backend.app.models.universal_agent_profile import UniversalAgentProfile
from backend.app.utils.llm_client import LLMClient, get_step_provider_model
from backend.app.utils.logger import get_logger
from backend.prompts.agent_generation_prompts import (
    AGENT_ELIGIBLE_FILTER_SYSTEM,
    AGENT_ELIGIBLE_FILTER_USER,
    AGENT_GENERATION_SYSTEM,
    AGENT_GENERATION_USER,
)

logger = get_logger(__name__)

_SCENARIO_ROLE_TEMPLATES: dict[str, tuple[str, ...]] = {
    "society": ("citizen", "official", "journalist", "activist", "institution", "rumor spreader"),
    "relationship": ("partner", "friend", "ex", "family member", "observer", "advisor"),
    "market": ("customer segment", "competitor", "regulator", "influencer", "sales team", "product team"),
}

# ---------------------------------------------------------------------------
# Entity types that qualify a KG node as a simulation agent
# ---------------------------------------------------------------------------

_AGENT_ELIGIBLE_TYPES: frozenset[str] = frozenset(
    {
        "Person",
        "Country",
        "Military",
        "Organization",
        "MediaOutlet",
        "PoliticalFigure",
        "Company",
        "NGO",
        "Institution",
        "Inferred",
        # Universal types for fiction, fantasy, interpersonal scenarios
        "Faction",
        "Family",
        "SecretSociety",
        "Creature",
        "Supernatural",
    }
)

# Fallback minimum agents when all LLM calls fail
_MIN_FALLBACK_AGENTS = 1

# Platform presets by entity type: (platform, base_activity_rate, anonymity_level)
_ENTITY_PLATFORM_MAP: dict[str, list[tuple[PlatformType, float, float]]] = {
    "Person": [
        (PlatformType.TWITTER, 0.7, 0.1),
        (PlatformType.REDDIT, 0.5, 0.3),
        (PlatformType.WECHAT, 0.6, 0.0),
    ],
    "Organization": [
        (PlatformType.TWITTER, 0.8, 0.0),
        (PlatformType.NEWS, 0.6, 0.0),
    ],
    "MediaOutlet": [
        (PlatformType.TWITTER, 0.9, 0.0),
        (PlatformType.NEWS, 0.95, 0.0),
    ],
    "PoliticalFigure": [
        (PlatformType.TWITTER, 0.85, 0.0),
        (PlatformType.NEWS, 0.7, 0.0),
        (PlatformType.WECHAT, 0.4, 0.0),
    ],
    "Country": [
        (PlatformType.NEWS, 0.9, 0.0),
        (PlatformType.TWITTER, 0.7, 0.0),
    ],
}

_CASUAL_STYLES: frozenset[str] = frozenset({"casual_gen_z", "informal_social", "emotional_expressive"})

_MODERATION_RISK_BY_ENTITY: dict[str, float] = {
    "Person": 0.03,
    "Organization": 0.005,
    "MediaOutlet": 0.002,
    "PoliticalFigure": 0.08,
    "Country": 0.001,
}


def _assign_platform_identities(
    agent_id: str,
    entity_type: str,
    communication_style: str,
    activity_level: float,
) -> tuple[PlatformIdentity, ...]:
    """Generate platform identities for an agent based on entity type and communication style."""
    presets = _ENTITY_PLATFORM_MAP.get(entity_type, _ENTITY_PLATFORM_MAP["Person"])

    if communication_style in _CASUAL_STYLES and entity_type == "Person":
        presets = [
            (PlatformType.TWITTER, 0.75, 0.15),
            (PlatformType.REDDIT, 0.70, 0.40),
            (PlatformType.FORUM, 0.55, 0.35),
            (PlatformType.WECHAT, 0.50, 0.05),
        ]

    mod_risk = _MODERATION_RISK_BY_ENTITY.get(entity_type, 0.03)

    identities = []
    for platform, base_rate, anonymity in presets:
        effective_rate = min(1.0, base_rate * activity_level * 2)
        identities.append(
            build_platform_identity(
                agent_id=agent_id,
                platform=platform,
                handle=f"{platform.value}_{agent_id[:12]}",
                base_activity_rate=max(0.01, effective_rate),
                anonymity_level=anonymity,
                audience_size=int(100 * activity_level * (2.0 if platform == PlatformType.TWITTER else 1.0)),
                tone_shift=0.05 if anonymity > 0.3 else 0.0,
                moderation_risk=mod_risk,
            )
        )
    return tuple(identities)


def _scenario_family_from_seed(seed_text: str) -> str:
    text = seed_text.lower()

    relationship_keywords = (
        "relationship", "couple", "dating", "marriage", "divorce", "friend", "family", "workplace tension",
        "romance", "partner", "breakup", "ex ", "mother", "father", "sibling",
    )
    market_keywords = (
        "company", "market", "competitor", "product", "customer", "startup", "brand", "sales",
        "enterprise", "regulator", "pricing", "launch", "market share", "supply chain",
    )

    if any(keyword in text for keyword in relationship_keywords):
        return "relationship"
    if any(keyword in text for keyword in market_keywords):
        return "market"
    return "society"


def _build_role_template_instruction(seed_text: str) -> str:
    family = _scenario_family_from_seed(seed_text)
    roles = ", ".join(_SCENARIO_ROLE_TEMPLATES[family])
    return (
        f"\n\nSCENARIO FAMILY: {family.upper()}\n"
        f"Prefer role coverage from this palette when it fits the evidence: {roles}.\n"
        "Do not force every role to appear, but make sure the final cast spans "
        "the key role types implied by the scenario."
    )


def _node_included_for_simulation(node: dict[str, Any]) -> bool:
    raw_props = node.get("properties", {})
    if isinstance(raw_props, str):
        try:
            props = json.loads(raw_props or "{}")
        except json.JSONDecodeError:
            props = {}
    elif isinstance(raw_props, dict):
        props = raw_props
    else:
        props = {}
    return props.get("include_in_simulation", True) is not False


def _normalise_edge_reference(edge: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = edge.get(key)
        if value:
            return str(value)
    return ""


def _graph_relationship_description(edge: dict[str, Any]) -> str:
    return (
        _normalise_edge_reference(edge, "description", "relation_type", "relation", "label")
        or "connected_to"
    )


def _merge_graph_relationships(
    profiles: list[UniversalAgentProfile],
    edges: list[dict[str, Any]],
) -> list[UniversalAgentProfile]:
    """Backfill inter-agent relationships directly from KG edges when possible."""
    if not profiles or not edges:
        return profiles

    by_node_id = {profile.kg_node_id: profile for profile in profiles}
    by_agent_id = {profile.id: profile for profile in profiles}
    merged: dict[str, list[tuple[str, str]]] = {
        profile.id: list(profile.relationships)
        for profile in profiles
    }

    for edge in edges:
        source_node_id = _normalise_edge_reference(edge, "source_id", "source")
        target_node_id = _normalise_edge_reference(edge, "target_id", "target")
        source_profile = by_node_id.get(source_node_id)
        target_profile = by_node_id.get(target_node_id)
        if not source_profile or not target_profile or source_profile.id == target_profile.id:
            continue

        relation = _graph_relationship_description(edge)
        pair = (target_profile.id, relation)
        if pair not in merged[source_profile.id]:
            merged[source_profile.id].append(pair)

    return [
        dc_replace(by_agent_id[agent_id], relationships=tuple(relationships))
        for agent_id, relationships in merged.items()
    ]


async def _load_persona_keys(graph_id: str) -> list[str]:
    """Load agent_type_key values from seed_persona_templates for graph_id."""
    from backend.app.utils.db import get_db  # noqa: PLC0415

    try:
        async with get_db() as db:
            rows = await db.execute_fetchall(
                "SELECT agent_type_key FROM seed_persona_templates WHERE graph_id = ?",
                (graph_id,),
            )
        return [r[0] for r in rows]
    except Exception:  # noqa: BLE001
        return []


# ---------------------------------------------------------------------------
# KGAgentFactory
# ---------------------------------------------------------------------------


class KGAgentFactory:
    """Generate UniversalAgentProfile instances from KG nodes and edges.

    Usage::

        factory = KGAgentFactory()
        profiles = await factory.generate_from_kg(
            nodes=kg_nodes,
            edges=kg_edges,
            seed_text="Iran nuclear negotiations 2024...",
            target_count=20,
        )
        csv_path = await factory.generate_agents_csv(profiles, "/tmp/agents.csv")
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        _persona_keys: frozenset[str] = frozenset(),
    ) -> None:
        self._llm = llm_client or LLMClient()
        self._persona_keys = _persona_keys

    @classmethod
    async def create(
        cls,
        graph_id: str,
        llm_client: LLMClient | None = None,
    ) -> KGAgentFactory:
        """Async factory that pre-loads persona keys for template alignment.

        Existing callers using KGAgentFactory() directly continue to work
        with _persona_keys=frozenset() (graceful degradation — no alignment).
        """
        keys = await _load_persona_keys(graph_id)
        return cls(llm_client=llm_client, _persona_keys=frozenset(keys))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_from_kg(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        seed_text: str,
        target_count: int | None = None,
    ) -> list[UniversalAgentProfile]:
        """Generate agent profiles from KG nodes and edges.

        Two-stage pipeline:
        1. Filter nodes down to agent-eligible actors via LLM.
        2. Generate full UniversalAgentProfile for each eligible node.

        If ``target_count`` exceeds the number of eligible nodes the LLM is
        instructed to invent additional plausible agents implied by the
        scenario (only if Cold Start conditions are met).

        Args:
            nodes: KG node dicts.
            edges: KG edge dicts.
            seed_text: Original scenario description.
            target_count: Desired total number of agents.

        Returns:
            A list of frozen ``UniversalAgentProfile`` instances.
        """
        if not nodes:
            raise ValueError("nodes must not be empty")

        nodes = [node for node in nodes if _node_included_for_simulation(node)]
        total_nodes = len(nodes)
        if not nodes:
            raise ValueError("nodes must not be empty after applying simulation filters")
        is_cold_start = total_nodes < 50

        logger.info(
            "generate_from_kg: %d nodes, %d edges, target_count=%s, cold_start=%s",
            total_nodes,
            len(edges),
            target_count,
            is_cold_start
        )

        # Stage 1 — eligibility filter
        eligible_nodes = await self._filter_agent_eligible_nodes(nodes)

        if not eligible_nodes:
            logger.warning(
                "No agent-eligible nodes found among %d KG nodes; falling back to all nodes",
                len(nodes),
            )
            eligible_nodes = nodes

        resolved_target = target_count if target_count is not None else len(eligible_nodes)

        # Stage 2 — profile generation
        profiles = await self._generate_profiles(
            eligible_nodes=eligible_nodes,
            edges=edges,
            seed_text=seed_text,
            target_count=resolved_target,
            is_cold_start=is_cold_start
        )

        logger.info("generate_from_kg complete: produced %d profiles", len(profiles))
        return profiles

    def generate_agents_csv(
        self,
        profiles: list[UniversalAgentProfile],
        output_path: str,
    ) -> str:
        """Write OASIS-compatible agents.csv to ``output_path``.

        The CSV has three columns: ``userid``, ``user_char``, ``username``.
        The file is created (or overwritten) at the given path.

        Args:
            profiles: Agent profiles to serialise.
            output_path: Absolute or relative path for the output CSV.

        Returns:
            The resolved absolute path of the written file.

        Raises:
            ValueError: If ``profiles`` is empty.
            OSError: If the file cannot be written.
        """
        if not profiles:
            raise ValueError("profiles must not be empty to write agents.csv")

        abs_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        rows = []
        for p in profiles:
            oasis_row = p.to_oasis_row()
            # Append platform-behavior notes so OASIS subprocess understands per-platform persona.
            if p.platform_identities:
                platform_notes = "; ".join(
                    f"{pi.platform.value}:{pi.handle}(anon={pi.anonymity_level:.1f},tone_shift={pi.tone_shift:+.2f})"
                    for pi in p.platform_identities
                )
                oasis_row = {**oasis_row, "user_char": f"{oasis_row['user_char']} [platforms: {platform_notes}]"}
            # OASIS agents_generator expects a 'description' column alongside user_char
            oasis_row["description"] = oasis_row["user_char"]
            rows.append(oasis_row)
        fieldnames = ["userid", "user_char", "username", "description"]

        with open(abs_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        logger.info("agents.csv written: %d rows → %s", len(rows), abs_path)
        return abs_path

    async def save_platform_identities_to_db(
        self,
        session_id: str,
        identities: list[PlatformIdentity],
    ) -> None:
        """Persist platform identities to the ``platform_identities`` DB table.

        Idempotent — uses INSERT OR REPLACE so re-runs don't duplicate rows.
        Best-effort: logs on failure but never raises.
        """
        if not identities:
            return
        try:
            from backend.app.utils.db import get_db  # noqa: PLC0415

            async with get_db() as db:
                for pi in identities:
                    await db.execute(
                        """
                        INSERT OR REPLACE INTO platform_identities
                            (session_id, agent_id, platform, handle,
                             anonymity_level, activity_vector_json,
                             audience_size, tone_shift, moderation_risk)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            session_id,
                            pi.agent_id,
                            pi.platform.value,
                            pi.handle,
                            pi.anonymity_level,
                            ",".join(str(v) for v in pi.activity_vector_24h),
                            pi.audience_size,
                            pi.tone_shift,
                            pi.moderation_risk,
                        ),
                    )
                await db.commit()
            logger.info(
                "save_platform_identities_to_db: %d rows for session=%s",
                len(identities),
                session_id,
            )
        except Exception:
            logger.exception(
                "save_platform_identities_to_db failed for session=%s — skipping",
                session_id,
            )

    # ------------------------------------------------------------------
    # Stage 1: eligibility filter
    # ------------------------------------------------------------------

    async def _filter_agent_eligible_nodes(
        self,
        nodes: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Use LLM to identify which KG nodes should become simulation agents.

        Falls back to a fast heuristic filter if the LLM call fails.

        Args:
            nodes: All KG nodes from GraphBuilder.

        Returns:
            Filtered list of node dicts (eligible agents only).
        """
        nodes_json = json.dumps(nodes, ensure_ascii=False, indent=2)

        _s2_provider, _s2_model = get_step_provider_model(2)
        try:
            result = await self._llm.chat_json(
                messages=[
                    {"role": "system", "content": AGENT_ELIGIBLE_FILTER_SYSTEM},
                    {
                        "role": "user",
                        "content": AGENT_ELIGIBLE_FILTER_USER.format(nodes_json=nodes_json),
                    },
                ],
                provider=_s2_provider,
                model=_s2_model,
                temperature=0.2,
                max_tokens=4096,
            )
            eligible_ids: set[str] = {
                str(entry["node_id"]) for entry in result.get("eligible", []) if "node_id" in entry
            }
            eligible = [n for n in nodes if str(n.get("id", "")) in eligible_ids and _node_included_for_simulation(n)]

            if not eligible:
                logger.warning("LLM filter returned 0 eligible nodes; using heuristic fallback")
                return self._heuristic_filter(nodes)

            return eligible

        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "LLM eligibility filter failed (%s); using heuristic fallback",
                exc,
            )
            return self._heuristic_filter(nodes)

    @staticmethod
    def _heuristic_filter(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Fast heuristic fallback when the LLM filter is unavailable.

        Keeps nodes whose ``entity_type`` is in the eligible set, or whose
        ``label`` / ``type`` field contains actor-like keywords.

        Args:
            nodes: All KG nodes.

        Returns:
            Subset likely to be concrete actors.
        """
        actor_keywords = frozenset(
            {
                "person",
                "people",
                "country",
                "nation",
                "government",
                "military",
                "army",
                "organization",
                "organisation",
                "company",
                "corporation",
                "media",
                "outlet",
                "party",
                "movement",
                "institution",
                "leader",
                "minister",
                "president",
                "figure",
            }
        )

        def _is_actor(node: dict[str, Any]) -> bool:
            entity_type = str(node.get("entity_type", "")).lower()
            label = str(node.get("label", "")).lower()
            node_type = str(node.get("type", "")).lower()
            combined = f"{entity_type} {label} {node_type}"
            return any(kw in combined for kw in actor_keywords)

        filtered = [n for n in nodes if _node_included_for_simulation(n) and _is_actor(n)]
        # If heuristic also returns nothing, accept all nodes as a last resort
        included_nodes = [n for n in nodes if _node_included_for_simulation(n)]
        return filtered if filtered else included_nodes

    # ------------------------------------------------------------------
    # Stage 2: profile generation
    # ------------------------------------------------------------------

    async def _generate_profiles(
        self,
        eligible_nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        seed_text: str,
        target_count: int,
        is_cold_start: bool = False,
    ) -> list[UniversalAgentProfile]:
        """Call LLM to generate full agent profiles for eligible nodes.

        Includes Cold Start intervention:
        - If is_cold_start=True: LLM is permitted to invent plausible agents (conf=0.1).
        - If is_cold_start=False: LLM MUST strictly use evidence from KG.
        """
        eligible_json = json.dumps(eligible_nodes, ensure_ascii=False, indent=2)
        edges_json = json.dumps(edges, ensure_ascii=False, indent=2)

        if is_cold_start:
            cold_start_instruction = (
                "\n\n[COLD START PROTOCOL: ACTIVE]\n"
                "The current knowledge graph is sparse. You are PERMITTED to hallucinate/invent "
                "plausible agents that are logically implied by the scenario but not explicitly in the KG nodes. "
                "For invented agents, use `confidence_score=0.1` in your internal reasoning."
            )
        else:
            cold_start_instruction = (
                "\n\n[COLD START PROTOCOL: INACTIVE]\n"
                "The knowledge graph is well-populated. You MUST STRICTLY limit your agents to those "
                "supported by explicit KG nodes or very direct evidence. Do NOT invent new characters."
            )

        user_message = AGENT_GENERATION_USER.format(
            seed_text=seed_text,
            eligible_nodes_json=eligible_json,
            edges_json=edges_json,
            target_count=target_count,
        ) + cold_start_instruction + _build_role_template_instruction(seed_text)

        # If persona keys are available, constrain agent type assignment
        if self._persona_keys:
            key_hint = ", ".join(sorted(self._persona_keys))
            agent_type_instruction = (
                f"\n\nIMPORTANT: For each agent, assign an `agent_type` from this list: "
                f"{key_hint}. Use the most semantically fitting key."
            )
            user_message = user_message + agent_type_instruction

        _s2_provider, _s2_model = get_step_provider_model(2)
        try:
            result = await self._llm.chat_json(
                messages=[
                    {"role": "system", "content": AGENT_GENERATION_SYSTEM},
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ],
                provider=_s2_provider,
                model=_s2_model,
                temperature=0.7,
                max_tokens=8192,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"LLM profile generation failed: {exc}") from exc

        raw_agents: list[dict[str, Any]] = result.get("agents", [])
        if not raw_agents:
            raise RuntimeError("LLM returned no agents in profile generation response")

        profiles: list[UniversalAgentProfile] = []
        for raw in raw_agents:
            profile = self._parse_agent_dict(raw)
            if profile is not None:
                profiles.append(profile)

        if not profiles:
            raise RuntimeError("No valid agent profiles could be parsed from LLM response")

        return _merge_graph_relationships(profiles, edges)


    # ------------------------------------------------------------------
    # Stage 3: cognitive fingerprint generation
    # ------------------------------------------------------------------

    async def generate_fingerprints(
        self,
        profiles: list,
        seed_text: str,
        active_metrics: tuple[str, ...],
    ) -> list:
        """Generate CognitiveFingerprint for each agent profile via batched LLM call.

        Args:
            profiles: Agent profiles to enrich with cognitive fingerprints.
            seed_text: Original scenario seed (for context).
            active_metrics: UniversalScenarioConfig metric IDs (for susceptibility keys).

        Returns:
            List of CognitiveFingerprint, one per profile. Falls back to defaults
            on partial LLM failure — never raises.
        """
        from backend.app.models.cognitive_fingerprint import CognitiveFingerprint  # noqa: PLC0415

        if not profiles:
            return []

        summaries = [{"agent_id": p.id, "name": p.name, "role": p.role, "entity_type": p.entity_type} for p in profiles]
        prompt_user = (
            f"Scenario: {seed_text[:400]}\n"
            f"Active metrics: {list(active_metrics)}\n\n"
            "For each agent below, generate a CognitiveFingerprint JSON with fields:\n"
            "- agent_id (string, must match input)\n"
            "- values (dict, 3-8 scenario-relevant moral/political axes, values 0-1)\n"
            "- info_diet (list of 1-3 info source tags relevant to scenario)\n"
            "- group_memberships (list of faction/group names, may be empty)\n"
            "- susceptibility (dict mapping active metric IDs to sensitivity 0-1)\n"
            "- confirmation_bias (float 0-1)\n"
            "- conformity (float 0-1)\n\n"
            f"Agents: {summaries}\n\n"
            'Return JSON: {"fingerprints": [...]}'
        )
        messages = [
            {"role": "system", "content": "You are a social psychology expert generating agent cognitive profiles."},
            {"role": "user", "content": prompt_user},
        ]

        _s2_provider, _s2_model = get_step_provider_model(2)
        try:
            raw = await self._llm.chat_json(messages, max_tokens=4096, temperature=0.3,
                                            provider=_s2_provider, model=_s2_model)
            fp_list = raw.get("fingerprints", [])
        except Exception:  # noqa: BLE001
            logger.warning("KGAgentFactory: fingerprint LLM call failed — using defaults")
            fp_list = []

        fp_by_id = {fp.get("agent_id"): fp for fp in fp_list if isinstance(fp, dict)}
        result = []

        for profile in profiles:
            fp_data = fp_by_id.get(profile.id, {})
            try:
                result.append(
                    CognitiveFingerprint(
                        agent_id=profile.id,
                        values=_parse_values(fp_data.get("values", {})),
                        info_diet=tuple(fp_data.get("info_diet", ["general"])),
                        group_memberships=tuple(fp_data.get("group_memberships", [])),
                        susceptibility={str(k): float(v) for k, v in fp_data.get("susceptibility", {}).items()},
                        confirmation_bias=float(fp_data.get("confirmation_bias", 0.5)),
                        conformity=float(fp_data.get("conformity", 0.5)),
                    )
                )
            except (ValueError, TypeError):
                result.append(_default_fingerprint(profile.id))

        return result

    # ------------------------------------------------------------------
    # Stage 3b: voice profile enrichment
    # ------------------------------------------------------------------

    async def enrich_voice_profiles(
        self,
        profiles: list[UniversalAgentProfile],
        seed_text: str,
    ) -> list[UniversalAgentProfile]:
        """Enrich each profile with voice/style fields via an LLM call.

        Adds ``communication_style``, ``vocabulary_hints``, and
        ``platform_persona`` to each profile using :func:`dataclasses.replace`.
        Never raises — profiles missing voice data retain their default empty
        values.

        Args:
            profiles:  Profiles to enrich (frozen; returns new instances).
            seed_text: Scenario context for the LLM prompt.

        Returns:
            New list of ``UniversalAgentProfile`` with voice fields populated.
        """
        from dataclasses import replace as dc_replace  # noqa: PLC0415

        valid_styles = frozenset(
            {
                "formal_academic",
                "casual_gen_z",
                "strategic_institutional",
                "emotional_personal",
                "analytical_professional",
                "activist_ideological",
            }
        )

        if not profiles:
            return []

        summaries = [{"agent_id": p.id, "name": p.name, "role": p.role, "entity_type": p.entity_type} for p in profiles]
        prompt_user = (
            f"Scenario: {seed_text[:400]}\n\n"
            "For each agent below, generate a voice profile JSON with fields:\n"
            "- agent_id (string, must match input)\n"
            '- communication_style: one of "formal_academic", "casual_gen_z",'
            ' "strategic_institutional", "emotional_personal",'
            ' "analytical_professional", "activist_ideological"\n'
            "- vocabulary_hints: list of 3-5 characteristic vocabulary or metaphor"
            ' types (short phrases), e.g. ["法律術語", "程序正義"] or'
            ' ["遊戲比喻", "Z世代流行語"]\n'
            "- platform_persona: 1-2 sentences describing how they post differently"
            ' on different platforms, e.g. "Facebook: 長篇分析，引用數據；'
            'Instagram: 短句+話題標籤，情緒化表達"\n\n'
            f"Agents: {summaries}\n\n"
            'Return JSON: {"voice_profiles": [...]}'
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a communications expert generating distinct voice profiles for simulation agents."
                ),
            },
            {"role": "user", "content": prompt_user},
        ]

        voice_by_id: dict[str, dict] = {}
        _s2_provider, _s2_model = get_step_provider_model(2)
        try:
            raw = await self._llm.chat_json(messages, max_tokens=2048, temperature=0.4,
                                            provider=_s2_provider, model=_s2_model)
            vp_list = raw.get("voice_profiles", [])
            for vp in vp_list:
                if isinstance(vp, dict) and vp.get("agent_id"):
                    voice_by_id[str(vp["agent_id"])] = vp
        except Exception:  # noqa: BLE001
            logger.warning("KGAgentFactory: voice profile LLM call failed — keeping defaults")

        enriched: list[UniversalAgentProfile] = []
        for profile in profiles:
            vd = voice_by_id.get(profile.id, {})
            try:
                raw_style = str(vd.get("communication_style", ""))
                comm_style = raw_style if raw_style in valid_styles else ""
                vocab_hints = tuple(str(h) for h in vd.get("vocabulary_hints", []) if h)[:5]
                plat_persona = str(vd.get("platform_persona", ""))
                enriched.append(
                    dc_replace(
                        profile,
                        communication_style=comm_style,
                        vocabulary_hints=vocab_hints,
                        platform_persona=plat_persona,
                    )
                )
            except (TypeError, ValueError):
                logger.debug("Voice field parse failed for agent %s — keeping defaults", profile.id)
                enriched.append(profile)

        return enriched

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_agent_dict(raw: dict[str, Any]) -> UniversalAgentProfile | None:
        """Parse a single raw agent dict into an UniversalAgentProfile.

        Returns ``None`` and logs a warning if the dict is missing required
        fields or contains invalid values.

        Args:
            raw: Dict from LLM response ``agents`` list.

        Returns:
            A frozen ``UniversalAgentProfile``, or ``None`` on parse error.
        """
        required = {"id", "name", "role", "entity_type", "persona"}
        missing = required - raw.keys()
        if missing:
            logger.warning("Skipping agent with missing fields %s: %r", missing, raw)
            return None

        try:
            # Convert stance_axes from dict to tuple-of-tuples
            raw_stance = raw.get("stance_axes", {})
            if isinstance(raw_stance, dict):
                stance_axes: tuple[tuple[str, float], ...] = tuple((str(k), float(v)) for k, v in raw_stance.items())
            else:
                stance_axes = tuple()

            # Convert relationships from dict or list to tuple-of-tuples
            raw_rels = raw.get("relationships", {})
            if isinstance(raw_rels, dict):
                relationships: tuple[tuple[str, str], ...] = tuple((str(k), str(v)) for k, v in raw_rels.items())
            elif isinstance(raw_rels, list):
                relationships = tuple((str(item[0]), str(item[1])) for item in raw_rels if len(item) >= 2)
            else:
                relationships = tuple()

            goals = tuple(str(g) for g in raw.get("goals", []))
            capabilities = tuple(str(c) for c in raw.get("capabilities", []))
            constraints = tuple(str(c) for c in raw.get("constraints", []))
            raw_beliefs = raw.get("beliefs", {})
            if isinstance(raw_beliefs, dict):
                beliefs: tuple[tuple[str, float], ...] = tuple(
                    (str(k), _clamp(float(v))) for k, v in raw_beliefs.items()
                )
            elif isinstance(raw_beliefs, list):
                beliefs = tuple((str(item), 0.5) for item in raw_beliefs if item)
            else:
                beliefs = tuple()

            agent_id = str(raw["id"])
            entity_type = str(raw["entity_type"])
            activity_level = _clamp(float(raw.get("activity_level", 0.5)))
            communication_style = str(raw.get("communication_style", ""))

            return UniversalAgentProfile(
                id=agent_id,
                name=str(raw["name"]),
                role=str(raw["role"]),
                entity_type=entity_type,
                persona=str(raw["persona"]),
                goals=goals,
                capabilities=capabilities,
                constraints=constraints,
                beliefs=beliefs,
                memory_seed=str(raw.get("memory_seed", "")),
                stance_axes=stance_axes,
                relationships=relationships,
                kg_node_id=str(raw.get("kg_node_id", raw["id"])),
                activity_level=activity_level,
                influence_weight=_clamp(float(raw.get("influence_weight", 1.0)), 0.0, 3.0),
                openness=_clamp(float(raw.get("openness", 0.5))),
                conscientiousness=_clamp(float(raw.get("conscientiousness", 0.5))),
                extraversion=_clamp(float(raw.get("extraversion", 0.5))),
                agreeableness=_clamp(float(raw.get("agreeableness", 0.5))),
                neuroticism=_clamp(float(raw.get("neuroticism", 0.5))),
                platform_identities=_assign_platform_identities(
                    agent_id=agent_id,
                    entity_type=entity_type,
                    communication_style=communication_style,
                    activity_level=activity_level,
                ),
            )

        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("Failed to parse agent dict: %s — %r", exc, raw)
            return None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp ``value`` to the range [lo, hi]."""
    return max(lo, min(hi, value))


def _parse_values(raw: dict) -> dict[str, float]:
    """Parse and validate values dict; returns 3-key default if invalid."""
    if not isinstance(raw, dict) or len(raw) < 3:
        return {"authority": 0.5, "openness": 0.5, "loyalty": 0.5}
    result = {}
    for k, v in list(raw.items())[:12]:
        try:
            result[str(k)] = max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            result[str(k)] = 0.5
    return result


def _default_fingerprint(agent_id: str):
    from backend.app.models.cognitive_fingerprint import CognitiveFingerprint  # noqa: PLC0415

    return CognitiveFingerprint(
        agent_id=agent_id,
        values={"authority": 0.5, "openness": 0.5, "loyalty": 0.5},
        info_diet=("general",),
        group_memberships=(),
        susceptibility={},
        confirmation_bias=0.5,
        conformity=0.5,
    )

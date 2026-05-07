"""First-use mode presets for society, relationship, and market scenarios."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModePreset:
    """Productised defaults for one prediction mode."""

    mode: str
    label: str
    scenario_type: str
    ontology: tuple[str, ...]
    role_templates: tuple[str, ...]
    report_mode: str
    default_metrics: tuple[str, ...]
    default_agent_count: int
    default_round_count: int
    description: str

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "label": self.label,
            "scenario_type": self.scenario_type,
            "ontology": list(self.ontology),
            "role_templates": list(self.role_templates),
            "report_mode": self.report_mode,
            "default_metrics": list(self.default_metrics),
            "default_agent_count": self.default_agent_count,
            "default_round_count": self.default_round_count,
            "description": self.description,
        }


_PRESETS: dict[str, ModePreset] = {
    "society": ModePreset(
        mode="society",
        label="Society Mode",
        scenario_type="society",
        ontology=("Person", "Organization", "Institution", "MediaOutlet", "Event", "Policy", "Issue"),
        role_templates=("citizen", "official", "journalist", "activist", "institution", "rumor spreader"),
        report_mode="social_forecast",
        default_metrics=("propagation", "trust", "polarization", "escalation_risk"),
        default_agent_count=120,
        default_round_count=12,
        description="Public opinion, policy reaction, crisis propagation, civic conflict.",
    ),
    "relationship": ModePreset(
        mode="relationship",
        label="Relationship Mode",
        scenario_type="relationship",
        ontology=("Person", "Family", "Group", "Event", "Issue", "Emotion", "Boundary"),
        role_templates=("partner", "friend", "ex", "family member", "observer", "advisor"),
        report_mode="relationship_forecast",
        default_metrics=("trust", "attachment_shift", "misunderstanding_risk", "repair_window"),
        default_agent_count=24,
        default_round_count=10,
        description="Couples, family, friendship, workplace interpersonal tension.",
    ),
    "market": ModePreset(
        mode="market",
        label="Market Mode",
        scenario_type="market",
        ontology=("Company", "Product", "CustomerSegment", "Competitor", "Regulator", "Channel", "Risk"),
        role_templates=("customer segment", "competitor", "regulator", "influencer", "sales team", "product team"),
        report_mode="market_launch_forecast",
        default_metrics=("adoption", "blockers", "competitor_response", "narrative_risk"),
        default_agent_count=80,
        default_round_count=10,
        description="Product launch, customer reaction, competitor response, company strategy.",
    ),
}


def list_mode_presets() -> list[dict]:
    """Return all first-use mode presets."""
    return [preset.to_dict() for preset in _PRESETS.values()]


def get_mode_preset(mode: str) -> dict:
    """Return one mode preset by id."""
    key = mode.lower().strip()
    if key not in _PRESETS:
        raise ValueError(f"Unknown mode: {mode}")
    return _PRESETS[key].to_dict()


def detect_mode_from_text(text: str) -> dict:
    """Cheap deterministic mode suggestion for first-use UX."""
    lowered = text.lower()
    if any(word in lowered for word in ("couple", "partner", "breakup", "family", "friend", "relationship")):
        return get_mode_preset("relationship")
    if any(word in lowered for word in ("product", "launch", "customer", "competitor", "pricing", "market")):
        return get_mode_preset("market")
    return get_mode_preset("society")

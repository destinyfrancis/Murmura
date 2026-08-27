"""Moderation dynamics engine.

Each simulation round, agents posting on a platform face platform-specific
content removal or shadow-ban. When moderated, the agent's neuroticism increases
(被打壓 → 激進化) modelled as a delta applied in the next EmotionalEngine update.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

# Platform-specific moderation base rates (additive on top of agent moderation_risk)
_PLATFORM_BASE_RATES: dict[str, float] = {
    "twitter": 0.03,
    "reddit": 0.015,
    "forum": 0.008,
    "wechat": 0.05,
    "news": 0.001,
}

# Shadow-ban vs hard-delete split probability
_SHADOW_BAN_PROBABILITY = 0.6

# Neuroticism increase upon moderation
_NEUROTICISM_DELTA_DELETE = 0.04
_NEUROTICISM_DELTA_SHADOW_BAN = 0.07


class ModerationEventType(str, Enum):
    DELETE = "delete"
    SHADOW_BAN = "shadow_ban"


@dataclass(frozen=True)
class ModerationEvent:
    """Immutable record of a moderation action against an agent."""

    agent_id: str
    platform: str
    event_type: ModerationEventType
    neuroticism_delta: float


class ModerationEngine:
    """Evaluate whether an agent's post is moderated in a given round.

    Usage:
        engine = ModerationEngine()
        event = engine.evaluate(agent_id, platform, moderation_risk, rng)
        if event:
            # apply event.neuroticism_delta to agent emotional state
    """

    def evaluate(
        self,
        agent_id: str,
        platform: str,
        moderation_risk: float,
        rng: random.Random,
    ) -> ModerationEvent | None:
        """Return a ModerationEvent if the agent's content is removed, else None.

        The effective moderation probability is agent moderation_risk + platform base rate.
        """
        base = _PLATFORM_BASE_RATES.get(platform, 0.02)
        effective_p = min(1.0, moderation_risk + base)

        if rng.random() >= effective_p:
            return None

        if rng.random() < _SHADOW_BAN_PROBABILITY:
            event_type = ModerationEventType.SHADOW_BAN
            delta = _NEUROTICISM_DELTA_SHADOW_BAN
        else:
            event_type = ModerationEventType.DELETE
            delta = _NEUROTICISM_DELTA_DELETE

        logger.debug(
            "Moderation: agent=%s platform=%s type=%s",
            agent_id, platform, event_type,
        )
        return ModerationEvent(
            agent_id=agent_id,
            platform=platform,
            event_type=event_type,
            neuroticism_delta=delta,
        )

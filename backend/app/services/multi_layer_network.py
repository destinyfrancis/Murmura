"""Multi-layer social network for platform-aware simulation.

Each platform (Twitter, Reddit, Forum, WeChat, News) is a separate edge layer.
Cross-platform belief propagation is delayed by CROSS_PLATFORM_LATENCY_ROUNDS
to simulate real-world information diffusion delays.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from backend.app.models.platform_identity import PlatformIdentity, PlatformType
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

# Cross-platform information diffusion latency in simulation rounds (1 round ≈ 1 hour)
CROSS_PLATFORM_LATENCY_ROUNDS: dict[tuple[PlatformType, PlatformType], int] = {
    (PlatformType.TWITTER, PlatformType.NEWS): 6,
    (PlatformType.TWITTER, PlatformType.REDDIT): 2,
    (PlatformType.TWITTER, PlatformType.WECHAT): 12,
    (PlatformType.REDDIT, PlatformType.TWITTER): 3,
    (PlatformType.REDDIT, PlatformType.NEWS): 8,
    (PlatformType.REDDIT, PlatformType.WECHAT): 18,
    (PlatformType.FORUM, PlatformType.TWITTER): 4,
    (PlatformType.FORUM, PlatformType.NEWS): 10,
    (PlatformType.NEWS, PlatformType.WECHAT): 6,
    (PlatformType.NEWS, PlatformType.TWITTER): 1,
    (PlatformType.WECHAT, PlatformType.FORUM): 8,
}


@dataclass(frozen=True)
class PlatformEdge:
    """Immutable directed edge in a platform's social graph."""

    source_id: str
    target_id: str
    platform: PlatformType
    weight: float  # influence weight [0.0, 1.0]


class MultiLayerNetwork:
    """Multi-layer social network with per-platform edge sets.

    Maintains one edge list per PlatformType and a lookup of which platforms
    each agent is active on (derived from registered PlatformIdentity objects).
    """

    def __init__(self) -> None:
        self._edges: dict[PlatformType, list[PlatformEdge]] = {p: [] for p in PlatformType}
        self._agent_platforms: dict[str, dict[PlatformType, PlatformIdentity]] = {}

    def add_edge(self, edge: PlatformEdge) -> None:
        self._edges[edge.platform].append(edge)

    def register_agent(self, platform_identity: PlatformIdentity) -> None:
        """Register a PlatformIdentity so the agent appears in platform selection."""
        agent_id = platform_identity.agent_id
        if agent_id not in self._agent_platforms:
            self._agent_platforms[agent_id] = {}
        self._agent_platforms[agent_id][platform_identity.platform] = platform_identity

    def get_edges(self, platform: PlatformType) -> list[PlatformEdge]:
        return list(self._edges[platform])

    def get_agent_platforms(self, agent_id: str) -> set[PlatformType]:
        return set(self._agent_platforms.get(agent_id, {}).keys())

    def select_platform_for_round(
        self,
        agent_id: str,
        hour: int,
        rng: random.Random,
    ) -> PlatformType | None:
        """Pick which platform the agent is active on for this round.

        Uses each platform identity's activity_vector_24h as a softmax weight.
        Returns None if the agent has no registered platform identities.
        """
        identities = self._agent_platforms.get(agent_id)
        if not identities:
            return None

        weights = {
            pt: pi.probability_at_hour(hour)
            for pt, pi in identities.items()
        }
        total = sum(weights.values())
        if total == 0:
            return rng.choice(list(weights.keys()))

        roll = rng.random() * total
        cumulative = 0.0
        for pt, w in weights.items():
            cumulative += w
            if roll <= cumulative:
                return pt
        return list(weights.keys())[-1]

    def get_platform_identity(
        self,
        agent_id: str,
        platform: PlatformType,
    ) -> PlatformIdentity | None:
        """Return the PlatformIdentity for agent_id on platform, or None."""
        return self._agent_platforms.get(agent_id, {}).get(platform)

    def get_cross_platform_latency(
        self,
        source: PlatformType,
        target: PlatformType,
    ) -> int:
        """Return simulation rounds of delay for cross-platform propagation."""
        if source == target:
            return 0
        return CROSS_PLATFORM_LATENCY_ROUNDS.get((source, target), 12)

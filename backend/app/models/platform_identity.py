"""Per-platform agent identity model.

Each agent can have up to one PlatformIdentity per PlatformType.
Activity vectors here OVERRIDE the global ActivityProfile vector
for rounds where that platform is selected.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PlatformType(str, Enum):
    TWITTER = "twitter"
    REDDIT = "reddit"
    FORUM = "forum"
    WECHAT = "wechat"
    NEWS = "news"


# Per-platform 24h activity templates (index 0 = midnight, 8 = 8AM)
# Captures real-world posting patterns per platform type.
PLATFORM_ACTIVITY_TEMPLATES: dict[PlatformType, tuple[float, ...]] = {
    # Twitter: spikes at morning commute (08-09) + lunch (12-13) + evening (20-22)
    PlatformType.TWITTER: (
        0.12, 0.06, 0.04, 0.03, 0.04, 0.10,  # 00-05
        0.25, 0.55, 0.80, 0.70, 0.60, 0.52,  # 06-11
        0.65, 0.58, 0.50, 0.48, 0.55, 0.62,  # 12-17
        0.70, 0.80, 0.90, 0.85, 0.60, 0.28,  # 18-23
    ),
    # Reddit: deep-dives, peaks late evening (21-01 AM)
    PlatformType.REDDIT: (
        0.42, 0.30, 0.18, 0.10, 0.06, 0.06,  # 00-05
        0.08, 0.18, 0.32, 0.40, 0.45, 0.42,  # 06-11
        0.38, 0.35, 0.35, 0.38, 0.45, 0.55,  # 12-17
        0.68, 0.80, 0.92, 1.00, 0.80, 0.58,  # 18-23
    ),
    # Forum/BBS: discussion boards, consistent daytime + evening
    PlatformType.FORUM: (
        0.20, 0.12, 0.08, 0.06, 0.06, 0.08,  # 00-05
        0.15, 0.30, 0.50, 0.60, 0.65, 0.60,  # 06-11
        0.55, 0.58, 0.60, 0.62, 0.65, 0.72,  # 12-17
        0.80, 0.88, 0.90, 0.82, 0.60, 0.35,  # 18-23
    ),
    # WeChat: peaks morning brief (07-09) + evening family time (20-22)
    PlatformType.WECHAT: (
        0.08, 0.05, 0.03, 0.03, 0.05, 0.15,  # 00-05
        0.35, 0.80, 0.90, 0.70, 0.55, 0.50,  # 06-11
        0.55, 0.48, 0.45, 0.45, 0.50, 0.58,  # 12-17
        0.65, 0.75, 0.88, 0.82, 0.55, 0.20,  # 18-23
    ),
    # News/media: publishing cycle peaks at 09 AM, 12 PM, 18 PM
    PlatformType.NEWS: (
        0.05, 0.03, 0.02, 0.02, 0.03, 0.08,  # 00-05
        0.20, 0.45, 0.72, 0.90, 0.85, 0.70,  # 06-11
        0.80, 0.65, 0.55, 0.50, 0.75, 0.85,  # 12-17
        0.65, 0.45, 0.30, 0.20, 0.12, 0.06,  # 18-23
    ),
}

_VECTOR_LEN = 24


@dataclass(frozen=True)
class PlatformIdentity:
    """Immutable per-platform identity for a simulation agent.

    Attributes:
        agent_id: Matches UniversalAgentProfile.id (str).
        platform: Which platform this identity represents.
        handle: Public username/handle on this platform.
        anonymity_level: 0.0 = real name, 1.0 = fully anonymous.
        activity_vector_24h: 24-dim hourly activity probability vector for this platform.
        audience_size: Approximate follower/subscriber count.
        tone_shift: Additive shift on neuroticism proxy (+= more extreme on this platform).
        moderation_risk: Per-round probability of content removal/shadow-ban.
    """

    agent_id: str
    platform: PlatformType
    handle: str
    anonymity_level: float
    activity_vector_24h: tuple[float, ...]
    audience_size: int
    tone_shift: float
    moderation_risk: float

    def __post_init__(self) -> None:
        if len(self.activity_vector_24h) != _VECTOR_LEN:
            raise ValueError(
                f"activity_vector_24h must have exactly {_VECTOR_LEN} elements, "
                f"got {len(self.activity_vector_24h)}"
            )
        if not (0.0 <= self.anonymity_level <= 1.0):
            raise ValueError(f"anonymity_level must be in [0,1], got {self.anonymity_level}")
        if not (0.0 <= self.moderation_risk <= 1.0):
            raise ValueError(f"moderation_risk must be in [0,1], got {self.moderation_risk}")

    def probability_at_hour(self, hour: int) -> float:
        """Activation probability at a given hour (0-23)."""
        if not 0 <= hour <= 23:
            return 0.0
        return self.activity_vector_24h[hour]


def build_platform_identity(
    agent_id: str,
    platform: PlatformType,
    handle: str,
    base_activity_rate: float = 0.7,
    anonymity_level: float = 0.1,
    audience_size: int = 200,
    tone_shift: float = 0.0,
    moderation_risk: float = 0.02,
) -> PlatformIdentity:
    """Build a PlatformIdentity using the platform's canonical activity template.

    Scales the template by base_activity_rate.
    """
    template = PLATFORM_ACTIVITY_TEMPLATES[platform]
    scaled = tuple(min(1.0, v * base_activity_rate) for v in template)
    return PlatformIdentity(
        agent_id=agent_id,
        platform=platform,
        handle=handle,
        anonymity_level=anonymity_level,
        activity_vector_24h=scaled,
        audience_size=audience_size,
        tone_shift=tone_shift,
        moderation_risk=moderation_risk,
    )

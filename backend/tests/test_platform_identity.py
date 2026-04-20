import dataclasses

import pytest
from backend.app.models.platform_identity import (
    PLATFORM_ACTIVITY_TEMPLATES,
    PlatformIdentity,
    PlatformType,
    build_platform_identity,
)


def test_platform_identity_immutable():
    pi = PlatformIdentity(
        agent_id="agent_001",
        platform=PlatformType.TWITTER,
        handle="@agent_001_tw",
        anonymity_level=0.2,
        activity_vector_24h=(0.1,) * 24,
        audience_size=500,
        tone_shift=0.1,
        moderation_risk=0.05,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        pi.handle = "changed"  # type: ignore[misc]


def test_build_platform_identity_uses_template():
    pi = build_platform_identity(
        agent_id="a1",
        platform=PlatformType.REDDIT,
        handle="u/a1_reddit",
        base_activity_rate=0.8,
    )
    assert len(pi.activity_vector_24h) == 24
    assert pi.platform == PlatformType.REDDIT


def test_activity_vector_length_validation():
    with pytest.raises(ValueError, match="24 elements"):
        PlatformIdentity(
            agent_id="a1",
            platform=PlatformType.WECHAT,
            handle="a1_wc",
            anonymity_level=0.0,
            activity_vector_24h=(0.5,) * 12,  # wrong length
            audience_size=50,
            tone_shift=0.0,
            moderation_risk=0.01,
        )


def test_platform_activity_templates_exist():
    for pt in PlatformType:
        assert pt in PLATFORM_ACTIVITY_TEMPLATES
        assert len(PLATFORM_ACTIVITY_TEMPLATES[pt]) == 24


def test_probability_at_hour_valid_and_boundary():
    pi = build_platform_identity(
        agent_id="a1",
        platform=PlatformType.TWITTER,
        handle="@a1",
        base_activity_rate=1.0,
    )
    # Valid hours return non-negative value
    assert pi.probability_at_hour(0) >= 0.0
    assert pi.probability_at_hour(23) >= 0.0
    # Out-of-range returns 0.0
    assert pi.probability_at_hour(24) == 0.0
    assert pi.probability_at_hour(-1) == 0.0


def test_build_platform_identity_scaling_correctness():
    rate = 0.8
    pi = build_platform_identity(
        agent_id="a2",
        platform=PlatformType.REDDIT,
        handle="u/a2",
        base_activity_rate=rate,
    )
    template = PLATFORM_ACTIVITY_TEMPLATES[PlatformType.REDDIT]
    expected_hour_21 = min(1.0, template[21] * rate)
    assert pi.activity_vector_24h[21] == pytest.approx(expected_hour_21)


def test_validation_rejects_out_of_range_values():
    base = dict(
        agent_id="a3",
        platform=PlatformType.FORUM,
        handle="a3_forum",
        anonymity_level=0.5,
        activity_vector_24h=(0.5,) * 24,
        audience_size=100,
        tone_shift=0.0,
        moderation_risk=0.02,
    )
    with pytest.raises(ValueError):
        PlatformIdentity(**{**base, "anonymity_level": 1.1})
    with pytest.raises(ValueError):
        PlatformIdentity(**{**base, "moderation_risk": -0.01})
    with pytest.raises(ValueError):
        PlatformIdentity(**{**base, "audience_size": -1})
    with pytest.raises(ValueError):
        build_platform_identity("a3", PlatformType.FORUM, "a3", base_activity_rate=-0.5)


from backend.app.models.universal_agent_profile import UniversalAgentProfile


def test_universal_agent_profile_has_platform_identities():
    pi_tw = build_platform_identity("agent_x", PlatformType.TWITTER, "@agent_x", base_activity_rate=0.7)
    pi_rc = build_platform_identity("agent_x", PlatformType.REDDIT, "u/agent_x", base_activity_rate=0.6)

    profile = UniversalAgentProfile(
        id="agent_x",
        name="Test Agent",
        role="Analyst",
        entity_type="Person",
        persona="A careful analyst.",
        goals=("understand trends",),
        capabilities=("data analysis",),
        stance_axes=(("support", 0.6),),
        relationships=(),
        kg_node_id="node_001",
        platform_identities=(pi_tw, pi_rc),
    )
    assert len(profile.platform_identities) == 2
    assert profile.get_platform_identity(PlatformType.TWITTER) == pi_tw
    assert profile.get_platform_identity(PlatformType.FORUM) is None


def test_universal_agent_profile_defaults_empty_platform_identities():
    profile = UniversalAgentProfile(
        id="agent_y",
        name="Y",
        role="r",
        entity_type="Person",
        persona="p",
        goals=(),
        capabilities=(),
        stance_axes=(),
        relationships=(),
        kg_node_id="n1",
    )
    assert profile.platform_identities == ()

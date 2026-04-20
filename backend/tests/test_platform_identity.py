import pytest
from backend.app.models.platform_identity import (
    PlatformIdentity,
    PlatformType,
    PLATFORM_ACTIVITY_TEMPLATES,
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
    with pytest.raises(Exception):
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

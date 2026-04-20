import dataclasses
import random

import pytest

from backend.app.models.activity_profile import ActivityProfile
from backend.app.models.platform_identity import PlatformType, build_platform_identity
from backend.app.services.temporal_activation import TemporalActivationService


def _make_profile(agent_id: int = 1) -> ActivityProfile:
    return ActivityProfile(
        agent_id=agent_id,
        chronotype="standard",
        activity_vector=(0.5,) * 24,
        base_activity_rate=0.8,
    )


def test_should_activate_with_zero_platform_vector_uses_floor():
    svc = TemporalActivationService()
    profile = _make_profile()
    pi = build_platform_identity(
        agent_id="1",
        platform=PlatformType.REDDIT,
        handle="u/test",
        base_activity_rate=1.0,
    )
    # Replace Reddit vector with all-zeros via dataclasses.replace
    silent_pi = dataclasses.replace(pi, activity_vector_24h=(0.0,) * 24)

    rng = random.Random(42)
    results = [
        svc.should_activate(profile, round_number=5, rng=rng, platform_identity=silent_pi)
        for _ in range(200)
    ]
    # With _MIN_ACTIVATION_P=0.05 floor, ~5% should be True even with zero vector
    # Just verify all return bool and no exception raised
    assert all(isinstance(r, bool) for r in results)
    # Should have some True (floor guarantees activation)
    assert any(results)


def test_should_activate_no_platform_identity_backward_compat():
    svc = TemporalActivationService()
    profile = _make_profile()
    rng = random.Random(0)
    # Old call signature without platform_identity still works
    result = svc.should_activate(profile, round_number=5, rng=rng)
    assert isinstance(result, bool)


def test_should_activate_platform_identity_overrides_profile():
    svc = TemporalActivationService(primetime_hours=frozenset(), primetime_multiplier=1.0)
    profile = _make_profile()  # activity_vector = (0.5,) * 24, rate=0.8 → p=0.4 at any hour

    # Platform identity with probability 1.0 at all hours
    pi_high = build_platform_identity(
        agent_id="1",
        platform=PlatformType.NEWS,
        handle="news_agent",
        base_activity_rate=1.0,
    )
    pi_always = dataclasses.replace(pi_high, activity_vector_24h=(1.0,) * 24)

    rng = random.Random(7)
    results_platform = [
        svc.should_activate(profile, round_number=3, rng=rng, platform_identity=pi_always)
        for _ in range(50)
    ]
    # With p=1.0 (no primetime), all should activate
    assert all(results_platform)

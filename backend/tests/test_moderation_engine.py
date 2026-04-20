import random

import pytest

from backend.app.services.moderation_engine import (
    ModerationEngine,
    ModerationEvent,
    ModerationEventType,
)


def test_no_moderation_with_zero_risk():
    engine = ModerationEngine()
    rng = random.Random(42)
    events = [
        engine.evaluate(
            agent_id="a1",
            platform="twitter",
            moderation_risk=0.0,
            rng=rng,
        )
        for _ in range(100)
    ]
    # platform base rate for twitter is 0.03 — with 100 samples some may trigger
    # but with zero agent risk, we test that base rate is small
    non_none = [e for e in events if e is not None]
    # At 3% base rate, expected ~3 events in 100. Extremely unlikely > 20.
    assert len(non_none) < 20


def test_always_moderated_with_risk_1():
    engine = ModerationEngine()
    rng = random.Random(0)
    events = [
        engine.evaluate(
            agent_id="a2",
            platform="reddit",
            moderation_risk=1.0,
            rng=rng,
        )
        for _ in range(20)
    ]
    assert all(e is not None for e in events)


def test_moderation_event_has_correct_fields():
    engine = ModerationEngine()
    rng = random.Random(1)
    event = engine.evaluate("a3", "forum", moderation_risk=1.0, rng=rng)
    assert event is not None
    assert isinstance(event, ModerationEvent)
    assert event.agent_id == "a3"
    assert event.platform == "forum"
    assert event.event_type in {ModerationEventType.DELETE, ModerationEventType.SHADOW_BAN}


def test_neuroticism_delta_positive_after_ban():
    engine = ModerationEngine()
    rng = random.Random(5)
    event = engine.evaluate("a4", "twitter", moderation_risk=1.0, rng=rng)
    assert event is not None
    assert event.neuroticism_delta > 0.0


def test_shadow_ban_has_higher_neuroticism_than_delete():
    from backend.app.services.moderation_engine import (
        _NEUROTICISM_DELTA_DELETE,
        _NEUROTICISM_DELTA_SHADOW_BAN,
    )
    assert _NEUROTICISM_DELTA_SHADOW_BAN > _NEUROTICISM_DELTA_DELETE


def test_unknown_platform_uses_default_base_rate():
    engine = ModerationEngine()
    rng = random.Random(0)
    # unknown platform "telegram" uses default 0.02 base rate — should not crash
    event = engine.evaluate("a5", "telegram", moderation_risk=1.0, rng=rng)
    assert event is not None


def test_moderation_engine_integration_smoke():
    """Verify ModerationEngine + neuroticism update contract."""
    engine = ModerationEngine()
    rng = random.Random(99)
    events = []
    for agent_id in ["a1", "a2", "a3"]:
        ev = engine.evaluate(agent_id, "wechat", moderation_risk=0.5, rng=rng)
        if ev:
            events.append(ev)
    for ev in events:
        assert 0 < ev.neuroticism_delta <= 0.1
        assert ev.platform == "wechat"

"""Honest pre-run cost availability for simulation sessions.

Murmura does not yet account for every OASIS/CAMEL call, hook, retry, or
model-specific token rate.  A numeric pre-run USD estimate would therefore be
misleading.  This module preserves the existing API shape while explicitly
reporting that no reliable estimate is available.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.utils.llm_client import _PROVIDERS


@dataclass(frozen=True)
class CostBreakdown:
    """Immutable pre-run cost-availability envelope."""

    provider: str
    model: str
    agent_count: int
    round_count: int
    estimated_input_tokens: int | None
    estimated_output_tokens: int | None
    estimated_cost_usd: float | None
    currency: str = "USD"
    status: str = "unavailable"
    reason: str = (
        "A reliable estimate needs measured model calls, tokens, retries, and "
        "provider pricing for this exact run."
    )


def estimate_cost(
    provider: str,
    model: str | None,
    agent_count: int,
    round_count: int,
) -> CostBreakdown:
    """Return an explicit unavailable estimate for a simulation run.

    Args:
        provider: LLM provider name (openrouter, fireworks, etc.)
        model: Model name override (uses provider default if None).
        agent_count: Number of agents.
        round_count: Number of simulation rounds.

    Returns:
        Immutable CostBreakdown without invented token or USD values.
    """
    cfg = _PROVIDERS.get(provider)
    resolved_model = model or (cfg or {}).get("default_model", "unknown")

    return CostBreakdown(
        provider=provider,
        model=resolved_model,
        agent_count=agent_count,
        round_count=round_count,
        estimated_input_tokens=None,
        estimated_output_tokens=None,
        estimated_cost_usd=None,
    )

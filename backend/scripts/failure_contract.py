"""Shared OASIS live-kernel failure contract helpers."""

from __future__ import annotations

import asyncio

FAILURE_ROUND_TIMEOUT = "round_timeout"
FAILURE_MODEL_CALL_FAILED = "model_call_failed"
FAILURE_NO_EFFECTIVE_ACTIONS = "no_effective_actions"
FAILURE_OASIS_RUNTIME_ERROR = "oasis_runtime_error"


def classify_failure(exc: BaseException | str) -> str:
    """Classify runtime failures into the public smoke-live contract."""
    if isinstance(exc, asyncio.TimeoutError):
        return FAILURE_ROUND_TIMEOUT
    message = str(exc).lower()
    if "no effective" in message or "no_effective" in message or "zero effective" in message:
        return FAILURE_NO_EFFECTIVE_ACTIONS
    if "timeout" in message or "timed out" in message:
        return FAILURE_ROUND_TIMEOUT
    if (
        "model" in message
        or "llm" in message
        or "api" in message
        or "rate limit" in message
        or "unauthorized" in message
        or "authentication" in message
        or "401" in message
    ):
        return FAILURE_MODEL_CALL_FAILED
    return FAILURE_OASIS_RUNTIME_ERROR

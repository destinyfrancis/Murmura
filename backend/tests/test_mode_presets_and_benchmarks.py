"""Tests for Stage 9/10/11 productisation surfaces."""

from __future__ import annotations

import json

from backend.app.services.mode_presets import detect_mode_from_text, get_mode_preset, list_mode_presets
from backend.scripts.run_upgrade_benchmarks import (
    run_gold_behavioral_benchmarks,
    run_smoke_benchmarks,
    run_upgrade_benchmarks,
    write_result,
)


def test_mode_presets_cover_three_first_class_modes():
    presets = {preset["mode"]: preset for preset in list_mode_presets()}
    assert {"society", "relationship", "market"} <= set(presets)
    assert presets["society"]["report_mode"] == "social_forecast"
    assert presets["relationship"]["report_mode"] == "relationship_forecast"
    assert presets["market"]["report_mode"] == "market_launch_forecast"


def test_mode_detection_selects_market_for_launch_text():
    preset = detect_mode_from_text("A startup product launch faces customer and competitor reaction")
    assert preset["mode"] == "market"


def test_unknown_mode_raises_clear_error():
    try:
        get_mode_preset("unknown")
    except ValueError as exc:
        assert "Unknown mode" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_upgrade_smoke_benchmark_writes_latest_result(tmp_path):
    result = run_smoke_benchmarks()
    output_path = write_result(result, tmp_path)

    assert output_path.exists()
    latest = tmp_path / "smoke_surface_latest.json"
    assert latest.exists()
    saved = json.loads(latest.read_text(encoding="utf-8"))
    assert saved["suite"] == "smoke_surface"
    assert saved["layer"] == "smoke_surface"
    assert saved["total"] >= 5


def test_gold_behavioral_benchmarks_score_three_fixtures():
    result = run_gold_behavioral_benchmarks()

    assert result["suite"] == "gold_behavioral"
    assert result["total"] == 3
    assert result["passed"] == 3
    assert {fixture["mode"] for fixture in result["fixtures"]} == {"society", "relationship", "market"}


def test_upgrade_benchmark_output_has_two_layers():
    result = run_upgrade_benchmarks()

    assert result["suite"] == "upgrade_benchmarks"
    assert {"smoke_surface", "gold_behavioral"} == set(result["layers"])

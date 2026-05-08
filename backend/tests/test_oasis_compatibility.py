"""Tests for OASIS runtime capability detection."""

from __future__ import annotations

from pathlib import Path

from backend.app.services.oasis_compatibility import _detect_oasis_compatibility


def test_detect_oasis_missing_disables_simulation() -> None:
    result = _detect_oasis_compatibility(
        version_info=(3, 11),
        python_bin=Path("/tmp/python311"),
        import_probe=lambda _path: (False, "No module named oasis"),
    )

    assert result["available"] is False
    assert result["reason"] == "oasis_missing"
    assert result["oasis_importable"] is False


def test_detect_oasis_importable_enables_simulation() -> None:
    result = _detect_oasis_compatibility(
        version_info=(3, 11),
        python_bin=Path("/tmp/python311"),
        import_probe=lambda _path: (True, ""),
    )

    assert result["available"] is True
    assert result["reason"] == ""
    assert result["oasis_importable"] is True


def test_detect_unsupported_python_disables_even_if_oasis_imports() -> None:
    result = _detect_oasis_compatibility(
        version_info=(3, 12),
        python_bin=Path("/tmp/python312"),
        import_probe=lambda _path: (True, ""),
    )

    assert result["available"] is False
    assert result["reason"] == "python_3_12_unsupported"
    assert result["oasis_importable"] is False

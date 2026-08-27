from __future__ import annotations

from pathlib import Path

from backend.app.utils.db import _resolve_db_path


def test_resolve_db_path_migrates_legacy_file(tmp_path: Path) -> None:
    legacy_path = tmp_path / "murmuroscope.db"
    legacy_path.write_text("legacy", encoding="utf-8")

    resolved = _resolve_db_path(str(tmp_path / "murmura.db"))

    assert resolved == tmp_path / "murmura.db"
    assert resolved.exists()
    assert not legacy_path.exists()
    assert resolved.read_text(encoding="utf-8") == "legacy"


def test_resolve_db_path_keeps_existing_new_file(tmp_path: Path) -> None:
    new_path = tmp_path / "murmura.db"
    legacy_path = tmp_path / "murmuroscope.db"
    new_path.write_text("new", encoding="utf-8")
    legacy_path.write_text("legacy", encoding="utf-8")

    resolved = _resolve_db_path(str(new_path))

    assert resolved == new_path
    assert resolved.read_text(encoding="utf-8") == "new"
    assert legacy_path.exists()

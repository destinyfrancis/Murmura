from __future__ import annotations

import pytest

from backend.app.services.scenario_intake import ScenarioIntakeService


def test_from_text_chunks_long_input_with_offsets() -> None:
    service = ScenarioIntakeService(chunk_chars=20, chunk_overlap=5)
    result = service.from_text("Alpha beta gamma.\n\nDelta epsilon zeta.\n\nEta theta iota.", source_ref="case.md")

    assert result.chunk_count > 1
    assert result.chunks[0].source_ref == "case.md"
    assert result.chunks[0].start_char == 0
    assert result.chunks[1].start_char < result.chunks[0].end_char


def test_from_bytes_accepts_markdown() -> None:
    result = ScenarioIntakeService().from_bytes(
        b"# Launch\n\nAlice challenges Bob.",
        filename="scenario.md",
    )

    assert result.filename == "scenario.md"
    assert result.content_type == "text/markdown"
    assert "Alice challenges Bob" in result.text


def test_from_bytes_rejects_unsupported_extension() -> None:
    with pytest.raises(ValueError, match="Unsupported file type"):
        ScenarioIntakeService().from_bytes(b"data", filename="scenario.docx")

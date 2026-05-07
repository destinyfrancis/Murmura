"""Scenario intake service for text and document uploads.

Normalises plain text, Markdown, TXT, and PDF input into a single text payload
plus deterministic chunks that downstream KG builders can cite as evidence.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from backend.app.utils.prompt_security import sanitize_seed_text

MAX_INTAKE_BYTES = 10 * 1024 * 1024
DEFAULT_CHUNK_CHARS = 6000
DEFAULT_CHUNK_OVERLAP = 500
SUPPORTED_EXTENSIONS = frozenset({".pdf", ".txt", ".md", ".markdown"})


@dataclass(frozen=True)
class IntakeChunk:
    """A deterministic slice of source text for evidence references."""

    index: int
    text: str
    start_char: int
    end_char: int
    source_ref: str


@dataclass(frozen=True)
class ScenarioIntakeResult:
    """Normalised scenario text and source chunks."""

    text: str
    chunks: tuple[IntakeChunk, ...]
    filename: str | None = None
    size_bytes: int | None = None
    content_type: str = "text/plain"

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)


class ScenarioIntakeService:
    """Extract and chunk scenario source material."""

    def __init__(
        self,
        *,
        max_bytes: int = MAX_INTAKE_BYTES,
        chunk_chars: int = DEFAULT_CHUNK_CHARS,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        self._max_bytes = max_bytes
        self._chunk_chars = chunk_chars
        self._chunk_overlap = min(chunk_overlap, max(0, chunk_chars - 1))

    def from_text(self, text: str, *, source_ref: str = "pasted_text") -> ScenarioIntakeResult:
        """Normalise pasted text into chunks."""
        raw_text = text or ""
        clean_text = sanitize_seed_text(raw_text, max_len=max(len(raw_text), 1))
        if not clean_text.strip():
            raise ValueError("seed_text is required")
        chunks = self.chunk_text(clean_text, source_ref=source_ref)
        return ScenarioIntakeResult(text=clean_text, chunks=tuple(chunks), filename=None, size_bytes=len(clean_text))

    def from_bytes(
        self,
        raw: bytes,
        *,
        filename: str | None,
        content_type: str | None = None,
    ) -> ScenarioIntakeResult:
        """Extract text from supported upload bytes and chunk it."""
        if len(raw) > self._max_bytes:
            raise ValueError("File exceeds 10 MB limit")

        file_name = filename or "upload.txt"
        ext = Path(file_name).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type '{ext}'. Allowed: PDF, TXT, Markdown")

        if ext == ".pdf":
            text = self._extract_pdf_text(raw)
            detected_content_type = "application/pdf"
        else:
            text = self._decode_text(raw)
            detected_content_type = "text/markdown" if ext in {".md", ".markdown"} else "text/plain"

        clean_text = sanitize_seed_text(text, max_len=max(len(text), 1))
        if not clean_text.strip():
            raise ValueError("Could not extract text from file")

        chunks = self.chunk_text(clean_text, source_ref=file_name)
        return ScenarioIntakeResult(
            text=clean_text,
            chunks=tuple(chunks),
            filename=file_name,
            size_bytes=len(raw),
            content_type=content_type or detected_content_type,
        )

    def chunk_text(self, text: str, *, source_ref: str) -> list[IntakeChunk]:
        """Split text into stable overlapping character chunks."""
        if len(text) <= self._chunk_chars:
            return [IntakeChunk(index=0, text=text, start_char=0, end_char=len(text), source_ref=source_ref)]

        chunks: list[IntakeChunk] = []
        start = 0
        index = 0
        while start < len(text):
            raw_end = min(len(text), start + self._chunk_chars)
            end = self._prefer_boundary(text, start, raw_end)
            if end <= start:
                end = raw_end
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    IntakeChunk(
                        index=index,
                        text=chunk_text,
                        start_char=start,
                        end_char=end,
                        source_ref=source_ref,
                    )
                )
                index += 1
            if end >= len(text):
                break
            next_start = max(0, end - self._chunk_overlap)
            if next_start <= start:
                next_start = end
            start = next_start
        return chunks

    def _prefer_boundary(self, text: str, start: int, raw_end: int) -> int:
        """Prefer paragraph/sentence boundaries near the chunk end."""
        if raw_end >= len(text):
            return raw_end
        window_start = max(start, raw_end - 800)
        window = text[window_start:raw_end]
        for marker in ("\n\n", "\n", "。", ".", "！", "?", "？"):
            pos = window.rfind(marker)
            if pos >= 0:
                candidate = window_start + pos + len(marker)
                if candidate - start >= max(1, self._chunk_chars // 2):
                    return candidate
        return raw_end

    def _decode_text(self, raw: bytes) -> str:
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1", errors="replace")

    def _extract_pdf_text(self, raw: bytes) -> str:
        try:
            import pypdf  # noqa: PLC0415

            reader = pypdf.PdfReader(io.BytesIO(raw))
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            pass

        try:
            import PyPDF2  # noqa: PLC0415, N813

            reader = PyPDF2.PdfReader(io.BytesIO(raw))
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError as exc:
            raise ValueError("PDF library not installed. Please upload TXT or Markdown.") from exc
        except Exception as exc:
            raise ValueError(f"PDF extraction failed: {exc}") from exc

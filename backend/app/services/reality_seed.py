"""Reality seed dossier generation for Step 0 scenario intake.

Turns a plain topic + simulation requirement into a sourced seed document
that can be reviewed by the user, exported as PDF, and fed into Graph Build.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from uuid import uuid4

import feedparser
import httpx
from bs4 import BeautifulSoup

from backend.app.services.scenario_intake import ScenarioIntakeService
from backend.app.services.runtime_settings import get_override
from backend.app.utils.llm_client import LLMClient, get_report_provider_model, get_step_provider_model
from backend.app.utils.logger import get_logger
from backend.app.utils.prompt_security import sanitize_seed_text

logger = get_logger("reality_seed")

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SEED_DIR = _PROJECT_ROOT / "data" / "reality_seeds"
_MAX_SOURCES = 12
_HTTP_TIMEOUT = 12.0


@dataclass(frozen=True)
class RealitySource:
    title: str
    url: str
    source: str
    published_at: str
    summary: str

    def to_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class RealitySeedResult:
    dossier_id: str
    title: str
    markdown: str
    seed_text: str
    pdf_path: str | None
    sources: tuple[RealitySource, ...]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dossier_id": self.dossier_id,
            "title": self.title,
            "markdown": self.markdown,
            "seed_text": self.seed_text,
            "pdf_path": self.pdf_path,
            "pdf_url": f"/api/reality-seed/{self.dossier_id}/pdf" if self.pdf_path else None,
            "sources": [s.to_dict() for s in self.sources],
            "generated_at": self.generated_at,
        }


class RealitySeedService:
    """Generate a latest-data seed dossier from topic, requirement, and documents."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    async def generate(
        self,
        *,
        topic: str,
        simulation_requirement: str,
        user_source_text: str = "",
        include_latest: bool = True,
        export_pdf: bool = True,
    ) -> RealitySeedResult:
        clean_topic = sanitize_seed_text(topic, max_len=800)
        clean_requirement = sanitize_seed_text(simulation_requirement, max_len=2000)
        clean_user_text = sanitize_seed_text(user_source_text, max_len=max(len(user_source_text), 1)) if user_source_text else ""
        if not clean_topic.strip():
            raise ValueError("topic is required")
        if not clean_requirement.strip():
            raise ValueError("simulation_requirement is required")

        sources: tuple[RealitySource, ...] = ()
        if include_latest:
            sources = await self._collect_latest_sources(clean_topic, clean_requirement)

        generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
        markdown = await self._build_dossier(
            topic=clean_topic,
            simulation_requirement=clean_requirement,
            user_source_text=clean_user_text,
            sources=sources,
            generated_at=generated_at,
        )
        title = _extract_title(markdown) or f"Reality Seed: {clean_topic[:80]}"
        dossier_id = str(uuid4())
        seed_text = _build_seed_text(
            topic=clean_topic,
            simulation_requirement=clean_requirement,
            markdown=markdown,
            sources=sources,
            generated_at=generated_at,
        )

        pdf_path: str | None = None
        if export_pdf:
            pdf_path = await self._write_pdf(dossier_id, title, markdown)

        await self._write_markdown(dossier_id, markdown)
        return RealitySeedResult(
            dossier_id=dossier_id,
            title=title,
            markdown=markdown,
            seed_text=seed_text,
            pdf_path=pdf_path,
            sources=sources,
            generated_at=generated_at,
        )

    async def from_upload(self, raw: bytes, filename: str | None, content_type: str | None) -> str:
        intake = ScenarioIntakeService().from_bytes(raw, filename=filename, content_type=content_type)
        return intake.text

    async def _collect_latest_sources(self, topic: str, requirement: str) -> tuple[RealitySource, ...]:
        query = f"{topic} {requirement}"
        google_task = self._fetch_google_news(query)
        gdelt_task = self._fetch_gdelt(query)
        results = await _gather_sources(google_task, gdelt_task)

        seen: set[str] = set()
        deduped: list[RealitySource] = []
        for source in results:
            key = _normalise_url(source.url) or source.title.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(source)
            if len(deduped) >= _MAX_SOURCES:
                break
        return tuple(deduped)

    async def _fetch_google_news(self, query: str) -> list[RealitySource]:
        url = (
            "https://news.google.com/rss/search?"
            f"q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        )
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        sources: list[RealitySource] = []
        for entry in feed.entries[:_MAX_SOURCES]:
            sources.append(
                RealitySource(
                    title=_clean_text(entry.get("title", "Untitled")),
                    url=str(entry.get("link", "")),
                    source="Google News",
                    published_at=str(entry.get("published", "")),
                    summary=_clean_html(entry.get("summary", ""))[:900],
                )
            )
        return sources

    async def _fetch_gdelt(self, query: str) -> list[RealitySource]:
        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "sort": "datedesc",
            "maxrecords": "10",
        }
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get("https://api.gdeltproject.org/api/v2/doc/doc", params=params)
            resp.raise_for_status()
            data = resp.json()

        sources: list[RealitySource] = []
        for article in data.get("articles", [])[:_MAX_SOURCES]:
            sources.append(
                RealitySource(
                    title=_clean_text(str(article.get("title") or "Untitled")),
                    url=str(article.get("url") or ""),
                    source=str(article.get("sourceCountry") or article.get("domain") or "GDELT"),
                    published_at=str(article.get("seendate") or ""),
                    summary=_clean_text(str(article.get("sourceCollection") or article.get("domain") or "")),
                )
            )
        return sources

    async def _build_dossier(
        self,
        *,
        topic: str,
        simulation_requirement: str,
        user_source_text: str,
        sources: tuple[RealitySource, ...],
        generated_at: str,
    ) -> str:
        provider, model = _resolve_reality_seed_model()
        logger.info("RealitySeed: using llm provider=%s model=%s", provider, model)
        source_block = "\n".join(
            f"[{i + 1}] {s.title}\nSource: {s.source}\nDate: {s.published_at}\nURL: {s.url}\nSummary: {s.summary}"
            for i, s in enumerate(sources)
        ) or "No live sources were retrieved. Use only the user-provided material and mark live-data gaps."
        user_block = user_source_text[:10000] if user_source_text else "No user document supplied."

        system = (
            "You generate reality-grounded seed dossiers for a multi-agent public-opinion simulation engine. "
            "Use ONLY the supplied live-source snippets and user-provided materials. Do not rely on unstated "
            "training-memory facts. Separate verified facts, uncertain claims, disputed claims, and simulation "
            "assumptions. Write in Traditional Chinese unless source names must remain as-is."
        )
        prompt = f"""Topic:
{topic}

Simulation requirement:
{simulation_requirement}

Observation cutoff:
{generated_at}

Latest source snippets:
{source_block}

User-provided material:
{user_block}

Create a detailed seed dossier in Markdown with these exact sections:
# Reality Seed Dossier: <short topic title>
## 0. Simulation Requirement
## 1. Observation Cutoff & Source Notes
## 2. Verified Timeline
## 3. Current Situation Snapshot
## 4. Key Actors & Stakeholder Groups
## 5. Public Narratives & Factions
## 6. Platform Diffusion Assumptions
## 7. Metrics To Track
## 8. Candidate Shocks For Simulation
## 9. Uncertainties, Disputed Claims, And Data Gaps
## 10. Seed Text For Graph Build
## 11. Source Appendix

Make section 10 a compact 900-1600 word seed text suitable for entity extraction. Include source numbers like [1].
"""
        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        try:
            response = await self._llm.chat(
                messages,
                provider=provider,
                model=model,
                temperature=0.25,
                max_tokens=5000,
            )
        except httpx.HTTPStatusError as exc:
            fallback = _fallback_reality_seed_model(provider, model, exc)
            if fallback is None:
                raise
            fallback_provider, fallback_model = fallback
            logger.warning(
                "RealitySeed: provider/model failed, retrying provider=%s model=%s",
                fallback_provider,
                fallback_model,
            )
            response = await self._llm.chat(
                messages,
                provider=fallback_provider,
                model=fallback_model,
                temperature=0.25,
                max_tokens=5000,
            )
        return response.content.strip()

    async def _write_markdown(self, dossier_id: str, markdown: str) -> None:
        _SEED_DIR.mkdir(parents=True, exist_ok=True)
        path = _SEED_DIR / f"{dossier_id}.md"
        await _write_text(path, markdown)

    async def _write_pdf(self, dossier_id: str, title: str, markdown: str) -> str:
        _SEED_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = _SEED_DIR / f"{dossier_id}.pdf"
        try:
            from weasyprint import HTML  # noqa: PLC0415

            html_doc = _markdown_to_html_document(title, markdown)
            HTML(string=html_doc, base_url=str(_SEED_DIR)).write_pdf(str(pdf_path))
        except Exception:
            logger.exception("Failed to render reality seed PDF")
            raise
        return str(pdf_path)


async def _gather_sources(*coros: Any) -> list[RealitySource]:
    import asyncio

    gathered = await asyncio.gather(*coros, return_exceptions=True)
    sources: list[RealitySource] = []
    for item in gathered:
        if isinstance(item, Exception):
            logger.debug("Reality source fetch failed: %s", item)
            continue
        sources.extend(item)
    return sources


async def _write_text(path: Path, text: str) -> None:
    import asyncio

    await asyncio.to_thread(path.write_text, text, encoding="utf-8")


def _build_seed_text(
    *,
    topic: str,
    simulation_requirement: str,
    markdown: str,
    sources: tuple[RealitySource, ...],
    generated_at: str,
) -> str:
    section = _extract_section(markdown, "10. Seed Text For Graph Build")
    if not section:
        section = markdown[:6000]
    source_lines = "\n".join(f"- [{i + 1}] {s.title} ({s.published_at}) {s.url}" for i, s in enumerate(sources))
    return (
        f"Observation cutoff: {generated_at}\n"
        f"Topic: {topic}\n"
        f"Simulation requirement: {simulation_requirement}\n\n"
        f"{section.strip()}\n\n"
        "Source appendix:\n"
        f"{source_lines}"
    ).strip()


def _resolve_reality_seed_model() -> tuple[str, str]:
    """Choose a model for Step 0 dossier generation.

    Step 0 is report-like research synthesis. Prefer explicit Step 1 settings
    when present; otherwise use Step 4's report model override before falling
    back to global Step 1 routing. This avoids surprising users who configured
    report generation but left graph-build globals pointed at a different
    provider.
    """
    step1_provider = get_override("step1_llm_provider")
    step1_model = get_override("step1_llm_model")
    if step1_provider and step1_model:
        return step1_provider, step1_model

    step4_provider = get_override("step4_llm_provider")
    step4_model = get_override("step4_llm_model")
    if step4_provider and step4_model:
        return step4_provider, step4_model

    try:
        return get_report_provider_model()
    except Exception:
        return get_step_provider_model(1)


def _fallback_reality_seed_model(
    provider: str,
    model: str,
    exc: httpx.HTTPStatusError,
) -> tuple[str, str] | None:
    status = exc.response.status_code if exc.response is not None else 0
    if status not in {400, 404}:
        return None
    openrouter_key = get_override("api_key_openrouter")
    if not openrouter_key:
        return None
    fallback = ("openrouter", "deepseek/deepseek-chat-v3.1")
    if (provider, model) == fallback:
        return None
    return fallback


def _extract_title(markdown: str) -> str | None:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _extract_section(markdown: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        return ""
    rest = markdown[match.end() :]
    next_heading = re.search(r"^##\s+", rest, re.MULTILINE)
    return rest[: next_heading.start()] if next_heading else rest


def _clean_html(value: str) -> str:
    return _clean_text(BeautifulSoup(value or "", "html.parser").get_text(" "))


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _normalise_url(url: str) -> str:
    return (url or "").split("#", 1)[0].strip().lower()


def _markdown_to_html_document(title: str, markdown: str) -> str:
    body = _markdown_to_html(markdown)
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    @page {{ size: A4; margin: 18mm 16mm; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Noto Sans CJK TC", "Noto Sans CJK SC", sans-serif; color: #111; line-height: 1.58; }}
    h1 {{ font-size: 24px; margin: 0 0 14px; }}
    h2 {{ font-size: 16px; margin: 22px 0 8px; border-top: 1px solid #d8d2c7; padding-top: 12px; }}
    h3 {{ font-size: 13px; margin: 16px 0 6px; }}
    p, li {{ font-size: 10.5px; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; background: #f2eee7; padding: 1px 3px; }}
    ul, ol {{ padding-left: 18px; }}
    a {{ color: #244f74; text-decoration: none; }}
  </style>
</head>
<body>{body}</body>
</html>"""


def _markdown_to_html(markdown: str) -> str:
    parts: list[str] = []
    in_list = False
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if not line:
            if in_list:
                parts.append("</ul>")
                in_list = False
            continue
        if line.startswith("# "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h1>{html.escape(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h3>{html.escape(line[4:].strip())}</h3>")
        elif line.startswith(("- ", "* ")):
            if not in_list:
                parts.append("<ul>")
                in_list = True
            parts.append(f"<li>{_inline_markdown(line[2:].strip())}</li>")
        else:
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<p>{_inline_markdown(line)}</p>")
    if in_list:
        parts.append("</ul>")
    return "\n".join(parts)


def _inline_markdown(text: str) -> str:
    safe = html.escape(text)
    safe = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"`([^`]+)`", r"<code>\1</code>", safe)
    return safe

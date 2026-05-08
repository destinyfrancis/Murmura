"""Step 0 reality seed generation endpoints."""

from __future__ import annotations

from pathlib import Path

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.app.models.response import APIResponse
from backend.app.services.reality_seed import RealitySeedService
from backend.app.utils.logger import get_logger

router = APIRouter(prefix="/reality-seed", tags=["reality-seed"])
logger = get_logger("api.reality_seed")

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SEED_DIR = _PROJECT_ROOT / "data" / "reality_seeds"


@router.post("/generate", response_model=APIResponse)
async def generate_reality_seed(
    topic: str = Form(...),
    simulation_requirement: str = Form(...),
    include_latest: bool = Form(True),
    export_pdf: bool = Form(True),
    file: UploadFile | None = File(None),
) -> APIResponse:
    """Generate a source-grounded seed dossier from a topic and requirement."""
    try:
        user_text = ""
        if file is not None:
            raw = await file.read()
            user_text = await RealitySeedService().from_upload(raw, file.filename, file.content_type)

        result = await RealitySeedService().generate(
            topic=topic,
            simulation_requirement=simulation_requirement,
            user_source_text=user_text,
            include_latest=include_latest,
            export_pdf=export_pdf,
        )
        return APIResponse(success=True, data=result.to_dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response else 502
        provider_message = ""
        if exc.response is not None:
            try:
                provider_message = exc.response.json().get("error", {}).get("message", "")
            except Exception:
                provider_message = exc.response.text[:160]
        logger.exception("generate_reality_seed provider request failed")
        if status == 401:
            detail = "LLM provider authentication failed. Re-enter and test the API key in Settings."
            if provider_message:
                detail = f"{detail} Provider said: {provider_message}"
        else:
            detail = (
                f"LLM provider request failed ({status}). "
                "Check the provider/model selected for Reality Seed."
            )
        raise HTTPException(
            status_code=502,
            detail=detail,
        ) from exc
    except Exception as exc:
        logger.exception("generate_reality_seed failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/{dossier_id}/pdf")
async def get_reality_seed_pdf(dossier_id: str) -> FileResponse:
    """Download a generated reality seed PDF."""
    safe_id = "".join(ch for ch in dossier_id if ch.isalnum() or ch == "-")
    path = (_SEED_DIR / f"{safe_id}.pdf").resolve()
    if not str(path).startswith(str(_SEED_DIR.resolve())) or not path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(
        str(path),
        media_type="application/pdf",
        filename=f"reality-seed-{safe_id}.pdf",
    )

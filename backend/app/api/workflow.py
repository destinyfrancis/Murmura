"""Async workflow endpoints for one-click seed-to-simulation runs."""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.app.api.auth import UserProfile, get_optional_user
from backend.app.models.response import APIResponse
from backend.app.services.workflow_runner import WorkflowRunner
from backend.app.utils.logger import get_logger

router = APIRouter(prefix="/workflow", tags=["workflow"])
logger = get_logger("api.workflow")

_MAX_SEED_CHARS = 500_000
_QUICK_START_MAX_BYTES = 10 * 1024 * 1024


class WorkflowQuickStartRequest(BaseModel):
    seed_text: str
    scenario_question: str = ""
    preset: str = "fast"


@router.post("/quick-start", response_model=APIResponse)
async def create_quick_workflow(
    req: WorkflowQuickStartRequest,
    user: Annotated[UserProfile | None, Depends(get_optional_user)] = None,
) -> APIResponse:
    """Create a background workflow and return immediately."""
    seed_text = req.seed_text.strip()
    if not seed_text:
        raise HTTPException(status_code=400, detail="seed_text is required")
    if len(seed_text) > _MAX_SEED_CHARS:
        raise HTTPException(status_code=400, detail="seed_text exceeds 500,000 character limit")

    try:
        runner = WorkflowRunner()
        data = await runner.create_workflow(
            seed_text=seed_text,
            scenario_question=req.scenario_question,
            preset=req.preset,
            owner_id=user.id if user else None,
        )
        workflow_id = data["workflow_id"]
        asyncio.create_task(runner.run(workflow_id))
        return APIResponse(
            success=True,
            data={
                **data,
                "status_url": f"/api/workflow/{workflow_id}",
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("create_quick_workflow failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/quick-start/upload", response_model=APIResponse)
async def create_quick_workflow_upload(
    file: Annotated[UploadFile, File(...)],
    scenario_question: str = "",
    preset: str = "fast",
    user: Annotated[UserProfile | None, Depends(get_optional_user)] = None,
) -> APIResponse:
    """Create a background workflow from an uploaded PDF/TXT/MD seed."""
    try:
        content = await file.read()
        from backend.app.services.scenario_intake import ScenarioIntakeService  # noqa: PLC0415

        intake = ScenarioIntakeService(max_bytes=_QUICK_START_MAX_BYTES).from_bytes(
            content,
            filename=file.filename,
            content_type=file.content_type,
        )
        runner = WorkflowRunner()
        data = await runner.create_workflow(
            seed_text=intake.text,
            scenario_question=scenario_question,
            preset=preset,
            owner_id=user.id if user else None,
        )
        workflow_id = data["workflow_id"]
        asyncio.create_task(runner.run(workflow_id))
        return APIResponse(
            success=True,
            data={**data, "status_url": f"/api/workflow/{workflow_id}"},
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 400 if "Unsupported" in message or "10 MB" in message else 422
        raise HTTPException(status_code=status_code, detail=message) from exc
    except Exception as exc:
        logger.exception("create_quick_workflow_upload failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/{workflow_id}", response_model=APIResponse)
async def get_workflow(workflow_id: str) -> APIResponse:
    """Return workflow state and event history for live UI polling."""
    try:
        data = await WorkflowRunner().get_workflow(workflow_id)
        if data is None:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return APIResponse(success=True, data=data, meta={"workflow_id": workflow_id})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_workflow failed for %s", workflow_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc

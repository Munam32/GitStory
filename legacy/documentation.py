"""
api/routes/documentation.py

FastAPI router exposing the Auto-Documentation API.

Endpoints:
  POST /docs/generate          — start generation (async via Celery or background task)
  GET  /docs/{project_id}      — get latest docs for project
  GET  /docs/{project_id}/status — poll status
  GET  /docs/{doc_id}/export   — download ZIP
  GET  /docs/{doc_id}/readme   — download README.md
  GET  /docs/{doc_id}/module-map — get module map JSON
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response

from ...services.documentation.orchestration.documentation_service import DocumentationService
from ...services.documentation.schemas.models import (
    DocStatus,
    DocumentationRequest,
    DocumentationResponse,
    DocumentationResult,
)
from ...utils.logging import get_logger

log = get_logger(__name__)
router = APIRouter(prefix="/docs", tags=["documentation"])


# ── Dependency injection ──────────────────────────────────────────────────────

def get_doc_service() -> DocumentationService:
    return DocumentationService()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=DocumentationResponse, status_code=202)
async def generate_documentation(
    request: DocumentationRequest,
    background_tasks: BackgroundTasks,
    use_celery: bool = Query(default=False, description="Route to Celery worker instead"),
    svc: DocumentationService = Depends(get_doc_service),
) -> DocumentationResponse:
    """
    Kick off documentation generation.

    - For small repos: runs as a FastAPI BackgroundTask.
    - For large repos: set `use_celery=true` to route to the Celery queue.

    The response returns immediately with a `doc_id` that can be polled via
    GET /docs/{project_id}/status.
    """
    log.info(
        "generate_request",
        project_id=str(request.project_id),
        repo_path=request.repo_path,
        use_celery=use_celery,
    )

    if use_celery:
        return _dispatch_celery(request)

    # For smaller repos: run in FastAPI background task
    # Return a stub response immediately; client polls for completion
    from uuid import uuid4
    from ...services.documentation.schemas.models import DocumentationResult
    stub_id = uuid4()

    background_tasks.add_task(_run_in_background, svc, request)

    return DocumentationResponse(
        doc_id=stub_id,
        project_id=request.project_id,
        status=DocStatus.PENDING,
        message="Documentation generation started. Poll /docs/{project_id}/status for updates.",
    )


@router.get("/{project_id}", response_model=DocumentationResult)
async def get_documentation(
    project_id: UUID,
    svc: DocumentationService = Depends(get_doc_service),
) -> DocumentationResult:
    """Return the latest completed DocumentationResult for a project."""
    result = await svc.get_result(project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No documentation found for project")
    return result


@router.get("/{project_id}/status")
async def get_documentation_status(
    project_id: UUID,
    svc: DocumentationService = Depends(get_doc_service),
) -> JSONResponse:
    """Lightweight polling endpoint — returns only id + status + error."""
    result = await svc.get_result(project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No documentation found for project")
    return JSONResponse({
        "doc_id": str(result.id),
        "project_id": str(result.project_id),
        "status": result.status.value,
        "error": result.error,
        "generated_at": result.generated_at.isoformat() if result.generated_at else None,
    })


@router.get("/{doc_id}/export")
async def export_zip(
    doc_id: UUID,
    svc: DocumentationService = Depends(get_doc_service),
) -> Response:
    """Download all documentation as a ZIP archive."""
    data = await svc.export_zip(doc_id)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail="Documentation not found or not yet completed",
        )
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=docs_{doc_id}.zip"},
    )


@router.get("/{doc_id}/readme")
async def export_readme(
    doc_id: UUID,
    svc: DocumentationService = Depends(get_doc_service),
) -> Response:
    """Download the generated README.md."""
    data = await svc.export_readme(doc_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Documentation not found")
    return Response(
        content=data,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=README.md"},
    )


@router.get("/{doc_id}/module-map")
async def get_module_map(
    doc_id: UUID,
    svc: DocumentationService = Depends(get_doc_service),
) -> JSONResponse:
    """Return the module map JSON — consumed by RAG, frontend tree, etc."""
    result = await svc.get_result_by_id(doc_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Documentation not found")
    return JSONResponse(result.module_map)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _run_in_background(svc: DocumentationService, request: DocumentationRequest) -> None:
    """Background task wrapper with error logging."""
    try:
        await svc.generate(request)
    except Exception as exc:
        log.error("background_generation_failed", error=str(exc), exc_info=True)


def _dispatch_celery(request: DocumentationRequest) -> DocumentationResponse:
    """Send to Celery queue and return immediately."""
    from ...workers.documentation_worker import generate_documentation_task
    from uuid import uuid4

    task = generate_documentation_task.apply_async(
        kwargs={
            "project_id": str(request.project_id),
            "repo_path": request.repo_path,
            "branch": request.branch,
            "commit_sha": request.commit_sha,
            "user_id": str(request.user_id),
            "regenerate": request.regenerate,
        }
    )
    log.info("celery_task_dispatched", task_id=task.id)
    return DocumentationResponse(
        doc_id=uuid4(),  # placeholder until Celery writes the real one
        project_id=request.project_id,
        status=DocStatus.PENDING,
        message=f"Queued. Celery task: {task.id}",
    )

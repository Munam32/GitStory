"""
workers/documentation_worker.py

Celery task for async documentation generation.
Used for large repos where generation > 30 seconds would timeout HTTP.

Architecture:
  FastAPI route → enqueue task → return task_id
  Celery worker → picks up task → runs full pipeline
  Frontend → polls GET /docs/{project_id} until status = completed
"""
from __future__ import annotations

import asyncio
from uuid import UUID

from celery import Celery

from ..config import get_settings
from ..services.documentation.orchestration.documentation_service import DocumentationService
from ..services.documentation.schemas.models import DocumentationRequest
from ..utils.logging import get_logger, configure_logging

configure_logging()
log = get_logger(__name__)
settings = get_settings()

celery_app = Celery(
    "autodoc",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,           # re-queue on worker crash
    worker_prefetch_multiplier=1,  # one task at a time per worker
)


@celery_app.task(
    name="autodoc.generate_documentation",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def generate_documentation_task(
    self,
    project_id: str,
    repo_path: str,
    branch: str,
    commit_sha: str,
    user_id: str,
    regenerate: bool = False,
) -> dict:
    """
    Celery task wrapping the async DocumentationService.generate() call.
    Returns a dict with doc_id and status.
    """
    log.info(
        "celery_task_started",
        task_id=self.request.id,
        project_id=project_id,
    )

    request = DocumentationRequest(
        project_id=UUID(project_id),
        repo_path=repo_path,
        branch=branch,
        commit_sha=commit_sha,
        user_id=UUID(user_id),
        regenerate=regenerate,
    )

    svc = DocumentationService()

    try:
        response = asyncio.get_event_loop().run_until_complete(svc.generate(request))
    except Exception as exc:
        log.error("celery_task_failed", error=str(exc), exc_info=True)
        raise self.retry(exc=exc)

    log.info(
        "celery_task_complete",
        doc_id=str(response.doc_id),
        status=response.status,
    )
    return {
        "doc_id": str(response.doc_id),
        "project_id": str(response.project_id),
        "status": response.status.value,
        "message": response.message,
    }

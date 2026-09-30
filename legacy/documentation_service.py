"""
services/documentation/orchestration/documentation_service.py

The ONE public interface that AnalysisOrchestrator calls.
Internally it coordinates: parsing → IR → LLM generation → post-processing → storage → export.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from ..exporters.export_service import ExportService
from ..generators.llm_doc_generator import LLMDocGenerator
from ..generators.markdown_builder import validate_markdown
from ..parser.module_mapper import build_module_map
from ..parser.parser_service import ParserService
from ..schemas.models import (
    DocStatus,
    DocumentationRequest,
    DocumentationResponse,
    DocumentationResult,
)
from ....repositories.documentation_repository import DocumentationRepository
from ....utils.logging import get_logger

log = get_logger(__name__)


class DocumentationService:
    """
    High-level service consumed by FastAPI routes and Celery workers.

    Usage:
        svc = DocumentationService()
        response = await svc.generate(request)
    """

    def __init__(
        self,
        parser: ParserService | None = None,
        generator: LLMDocGenerator | None = None,
        exporter: ExportService | None = None,
        repo: DocumentationRepository | None = None,
    ) -> None:
        self._parser = parser or ParserService()
        self._generator = generator or LLMDocGenerator()
        self._exporter = exporter or ExportService()
        self._repo = repo or DocumentationRepository()

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate(self, request: DocumentationRequest) -> DocumentationResponse:
        """
        Full pipeline:
          1. Validate repo path
          2. Parse → IR
          3. Build module map
          4. LLM: README + module summaries + function docs
          5. Post-process / validate
          6. Persist to Supabase
          7. Return status

        This is designed to be called from a Celery task (async handoff)
        OR directly from FastAPI with BackgroundTasks for smaller repos.
        """
        doc_id = uuid4()
        result = DocumentationResult(
            id=doc_id,
            project_id=request.project_id,
            commit_sha=request.commit_sha,
            status=DocStatus.RUNNING,
        )

        # Persist PENDING → RUNNING immediately so the frontend can poll
        await self._repo.upsert(result)

        try:
            result = await self._run_pipeline(request, result)
        except Exception as exc:
            log.error(
                "documentation_pipeline_failed",
                doc_id=str(doc_id),
                error=str(exc),
                exc_info=True,
            )
            result.status = DocStatus.FAILED
            result.error = str(exc)
            await self._repo.upsert(result)
            return DocumentationResponse(
                doc_id=doc_id,
                project_id=request.project_id,
                status=DocStatus.FAILED,
                message=str(exc),
            )

        return DocumentationResponse(
            doc_id=result.id,
            project_id=result.project_id,
            status=result.status,
            message="Documentation generated successfully.",
        )

    async def get_result(self, project_id: UUID) -> DocumentationResult | None:
        return await self._repo.get_latest_for_project(project_id)

    async def get_result_by_id(self, doc_id: UUID) -> DocumentationResult | None:
        return await self._repo.get_by_id(doc_id)

    async def export_zip(self, doc_id: UUID) -> bytes | None:
        result = await self._repo.get_by_id(doc_id)
        if result is None or result.status != DocStatus.COMPLETED:
            return None
        return self._exporter.export_zip(result)

    async def export_readme(self, doc_id: UUID) -> bytes | None:
        result = await self._repo.get_by_id(doc_id)
        if result is None:
            return None
        return self._exporter.export_readme(result)

    # ── Pipeline ──────────────────────────────────────────────────────────────

    async def _run_pipeline(
        self,
        request: DocumentationRequest,
        result: DocumentationResult,
    ) -> DocumentationResult:

        # ── Step 1: Validate repo path ────────────────────────────────────────
        repo_path = Path(request.repo_path)
        if not repo_path.exists():
            raise FileNotFoundError(f"Repo path not found: {request.repo_path}")

        project_name = repo_path.name  # derive project name from folder name

        # ── Step 2: Parse → IR ────────────────────────────────────────────────
        log.info("pipeline_step", step="parsing", doc_id=str(result.id))
        ir = self._parser.parse(
            project_id=request.project_id,
            repo_path=request.repo_path,
            branch=request.branch,
            commit_sha=request.commit_sha,
        )

        # ── Step 3: Build module map ──────────────────────────────────────────
        log.info("pipeline_step", step="module_map", doc_id=str(result.id))
        result.module_map = build_module_map(ir.files)

        # ── Step 4: LLM generation ────────────────────────────────────────────
        log.info("pipeline_step", step="llm_generation", doc_id=str(result.id))

        readme, module_summaries, function_docs = await _gather_llm_outputs(
            self._generator, ir, project_name
        )

        result.readme_markdown = readme
        result.module_summaries = module_summaries
        result.function_docs = function_docs

        # ── Step 5: Post-process / validate ───────────────────────────────────
        log.info("pipeline_step", step="post_processing", doc_id=str(result.id))
        is_valid, warnings = validate_markdown(result.readme_markdown)
        if warnings:
            log.warning("markdown_warnings", warnings=warnings)

        # ── Step 6: Persist ───────────────────────────────────────────────────
        log.info("pipeline_step", step="persist", doc_id=str(result.id))
        result.status = DocStatus.COMPLETED
        result.generated_at = datetime.now(timezone.utc)
        await self._repo.upsert(result)

        log.info(
            "pipeline_complete",
            doc_id=str(result.id),
            functions=len(result.function_docs),
            summaries=len(result.module_summaries),
        )
        return result


# ── Concurrency helper ────────────────────────────────────────────────────────

import asyncio

async def _gather_llm_outputs(
    generator: LLMDocGenerator,
    ir,
    project_name: str,
):
    """Run README, module summaries, and function docs concurrently."""
    readme_task = generator.generate_readme(ir, project_name)
    summaries_task = generator.generate_module_summaries(ir.files)
    function_docs_task = generator.generate_function_docs(ir.files)

    readme, summaries, function_docs = await asyncio.gather(
        readme_task, summaries_task, function_docs_task
    )
    return readme, summaries, function_docs

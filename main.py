from fastapi import FastAPI, HTTPException, BackgroundTasks
from uuid import UUID, uuid4
from datetime import datetime, timezone
import logging
import asyncio

from models import DocumentationRequest, DocumentationResponse, DocStatus, DocumentationResult
from parser_service import ParserService
from module_mapper import build_module_map
from llm_doc_generator import LLMDocGenerator
from documentation_repository import DocumentationRepository

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="GitStory Auto-Documentation API")

async def run_pipeline_background(request: DocumentationRequest, doc_id: UUID):
    """
    This function runs in the background AFTER the HTTP response is sent.
    """
    log.info(f"Background task started for {request.repo_path}")
    
    try:
        # 1. Parse Codebase
        parser = ParserService()
        ir = parser.parse(repo_path=request.repo_path, project_id=request.project_id)
        module_map = build_module_map(ir.files)
        
        # 2. LLM Generation via OpenRouter
        generator = LLMDocGenerator()
        readme = await generator.generate_readme(ir, "Auto_Generated_Project")
        module_summaries = await generator.generate_module_summaries(ir.files)
        function_docs = await generator.generate_function_docs(ir.files)
        
        # 3. Save to Supabase
        repo = DocumentationRepository()
        result = DocumentationResult(
            id=doc_id,
            project_id=request.project_id,
            status=DocStatus.COMPLETED,
            readme_markdown=readme,
            module_map=module_map,
            module_summaries=module_summaries,
            function_docs=function_docs,
            generated_at=datetime.now(timezone.utc)
        )
        
        try:
            await repo.upsert(result)
            log.info(f"✅ Background task complete. Saved {doc_id} to database.")
        except Exception as db_exc:
            log.warning(f"Database save bypassed (waiting for keys): {db_exc}")

    except Exception as exc:
        log.error(f"❌ Background pipeline failed: {exc}")


@app.post("/api/generate", response_model=DocumentationResponse, status_code=202)
async def generate_documentation(request: DocumentationRequest, background_tasks: BackgroundTasks):
    """
    Instantly returns a 202 Accepted status and hands the heavy lifting 
    off to FastAPI's internal background task manager.
    """
    try:
        doc_id = uuid4()
        log.info(f"Queueing generation for path: {request.repo_path}")
        
        # Dispatch the task to FastAPI's built-in background queue
        background_tasks.add_task(run_pipeline_background, request, doc_id)
        
        # Return instantly (< 2 seconds) to satisfy SRS Section 5.1
        return DocumentationResponse(
            doc_id=doc_id, 
            project_id=request.project_id,
            status=DocStatus.PENDING,
            message="Task Queued Successfully via FastAPI BackgroundTasks."
        )

    except Exception as exc:
        log.error(f"Failed to queue task: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))
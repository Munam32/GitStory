import json
from datetime import datetime, timezone
from uuid import UUID
import logging

from supabase import AsyncClient, acreate_client

from config import get_settings
from models import DocStatus, DocumentationResult, FunctionDoc, ModuleSummary, ParameterInfo

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
settings = get_settings()

class DocumentationRepository:
    def __init__(self, client: AsyncClient | None = None) -> None:
        self._client = client

    async def _get_client(self) -> AsyncClient:
        if self._client is None:
            self._client = await acreate_client(
                settings.supabase_url,
                settings.supabase_service_key,
            )
        return self._client

    async def upsert(self, result: DocumentationResult) -> DocumentationResult:
        client = await self._get_client()
        row = _to_row(result)
        resp = await client.table("documentation_results").upsert(row, on_conflict="id").execute()
        if resp.data:
            return _from_row(resp.data[0])
        return result

    async def get_by_id(self, doc_id: UUID) -> DocumentationResult | None:
        client = await self._get_client()
        resp = await client.table("documentation_results").select("*").eq("id", str(doc_id)).limit(1).execute()
        if resp.data:
            return _from_row(resp.data[0])
        return None

    async def get_latest_for_project(self, project_id: UUID) -> DocumentationResult | None:
        client = await self._get_client()
        resp = await client.table("documentation_results").select("*").eq("project_id", str(project_id)).order("created_at", desc=True).limit(1).execute()
        if resp.data:
            return _from_row(resp.data[0])
        return None

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _to_row(result: DocumentationResult) -> dict:
    return {
        "id": str(result.id),
        "project_id": str(result.project_id),
        "commit_sha": result.commit_sha,
        "status": result.status.value,
        "readme_markdown": result.readme_markdown,
        "module_map": result.module_map,
        "function_docs": [d.model_dump() for d in result.function_docs],
        "module_summaries": [s.model_dump() for s in result.module_summaries],
        "generated_at": result.generated_at.isoformat() if result.generated_at else None,
        "error": result.error,
        "updated_at": _now(),
    }

def _from_row(row: dict) -> DocumentationResult:
    func_docs = [
        FunctionDoc(
            function_name=d["function_name"],
            file=d["file"],
            parameters=[ParameterInfo(**p) for p in d.get("parameters", [])],
            returns=d.get("returns"),
            summary=d.get("summary", ""),
        )
        for d in (row.get("function_docs") or [])
    ]

    summaries = [ModuleSummary(**s) for s in (row.get("module_summaries") or [])]

    generated_at = None
    if row.get("generated_at"):
        generated_at = datetime.fromisoformat(row["generated_at"])

    return DocumentationResult(
        id=UUID(row["id"]),
        project_id=UUID(row["project_id"]),
        commit_sha=row.get("commit_sha", ""),
        status=DocStatus(row["status"]),
        readme_markdown=row.get("readme_markdown", ""),
        module_map=row.get("module_map") or {},
        function_docs=func_docs,
        module_summaries=summaries,
        generated_at=generated_at,
        error=row.get("error"),
    )
from __future__ import annotations

import asyncio
from pathlib import Path
import logging

from llm_client import LLMClient, LLMError
from templates import (
    build_function_doc_prompt,
    build_module_summary_prompt,
    build_readme_prompt,
)
from models import (
    FileInfo,
    FunctionDoc,
    ModuleSummary,
    ParameterInfo,
    RepositoryStructure,
)

# Use standard logging for the local prototype
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_MAX_CONCURRENCY = 1 # Throttled for OpenRouter Free Tier

class LLMDocGenerator:
    def __init__(self, client: LLMClient | None = None) -> None:
        self._client = client or LLMClient()

    async def generate_readme(self, ir: RepositoryStructure, project_name: str) -> str:
        prompt = build_readme_prompt(ir, project_name)
        try:
            return await self._client.complete(prompt, max_tokens=2500)
        except LLMError as exc:
            log.error(f"readme_generation_failed: {exc}")
            return _fallback_readme(project_name, ir)

    async def generate_module_summaries(self, files: list[FileInfo]) -> list[ModuleSummary]:
        semaphore = asyncio.Semaphore(_MAX_CONCURRENCY)

        async def _generate_one(file_info: FileInfo) -> ModuleSummary | None:
            async with semaphore:
                await asyncio.sleep(4) # Pace requests to stay under 20/min
                return await self._generate_module_summary(file_info)

        tasks = [_generate_one(f) for f in files if self._is_worth_documenting(f)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        summaries: list[ModuleSummary] = []
        for r in results:
            if isinstance(r, ModuleSummary):
                summaries.append(r)
            elif isinstance(r, Exception):
                # FIXED: Standard logging formatting
                log.warning(f"module_summary_task_failed: {str(r)}")
        return summaries

    async def generate_function_docs(self, files: list[FileInfo]) -> list[FunctionDoc]:
        semaphore = asyncio.Semaphore(_MAX_CONCURRENCY)

        async def _generate_one(file_info: FileInfo) -> list[FunctionDoc]:
            async with semaphore:
                await asyncio.sleep(4) # Pace requests to stay under 20/min
                return await self._generate_file_function_docs(file_info)

        tasks = [_generate_one(f) for f in files if self._has_public_symbols(f)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_docs: list[FunctionDoc] = []
        for r in results:
            if isinstance(r, list):
                all_docs.extend(r)
            elif isinstance(r, Exception):
                # FIXED: Standard logging formatting
                log.warning(f"function_doc_task_failed: {str(r)}")
        return all_docs

    async def _generate_module_summary(self, file_info: FileInfo) -> ModuleSummary:
        prompt = build_module_summary_prompt(file_info)
        try:
            # FIXED: Bumped max_tokens from 512 to 1500 to prevent cutoff
            data = await self._client.complete_json(prompt, max_tokens=1500)
            if not isinstance(data, dict):
                raise LLMError("Expected dict response")
            return ModuleSummary(
                file=file_info.path,
                purpose=data.get("purpose", ""),
                workflow=data.get("workflow", ""),
                notes=data.get("notes", ""),
            )
        except LLMError as exc:
            # FIXED: Standard logging formatting
            log.warning(f"module_summary_failed for {file_info.path}: {exc}")
            return ModuleSummary(
                file=file_info.path,
                purpose="(generation failed)",
                workflow="",
            )

    async def _generate_file_function_docs(self, file_info: FileInfo) -> list[FunctionDoc]:
        prompt = build_function_doc_prompt(file_info)
        try:
            data = await self._client.complete_json(prompt, max_tokens=2000)
            if not isinstance(data, list):
                data = [data]
            return [_parse_function_doc(item, file_info) for item in data if item]
        except LLMError as exc:
            # FIXED: Standard logging formatting
            log.warning(f"function_doc_failed for {file_info.path}: {exc}")
            return []

    @staticmethod
    def _is_worth_documenting(file_info: FileInfo) -> bool:
        return bool(file_info.functions or file_info.classes)

    @staticmethod
    def _has_public_symbols(file_info: FileInfo) -> bool:
        public_funcs = [f for f in file_info.functions if not f.name.startswith("_")]
        return bool(public_funcs or file_info.classes)

def _parse_function_doc(item: dict, file_info: FileInfo) -> FunctionDoc:
    func_name = item.get("function_name", "unknown")
    params: list[ParameterInfo] = []

    for func in file_info.functions:
        if func.name == func_name:
            params = func.parameters
            break

    return FunctionDoc(
        function_name=func_name,
        file=item.get("file", file_info.path),
        parameters=params,
        returns=item.get("returns"),
        summary=item.get("summary", ""),
    )

def _fallback_readme(project_name: str, ir: RepositoryStructure) -> str:
    file_list = "\n".join(f"- `{f.path}`" for f in ir.files[:20])
    return f"""# {project_name}\n> *Documentation generated by GitStory.*\n\n## Overview\nContains {len(ir.files)} source files.\n\n## Files\n{file_list}\n"""
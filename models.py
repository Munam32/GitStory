from pydantic import BaseModel
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

class Language(str, Enum):
    PYTHON = "python"

class ParameterInfo(BaseModel):
    name: str
    type_hint: Optional[str] = None
    default: Optional[str] = None

class FunctionInfo(BaseModel):
    name: str
    parameters: List[ParameterInfo]
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = []
    line_start: int
    line_end: int
    is_async: bool = False
    is_method: bool = False

class ClassInfo(BaseModel):
    name: str
    bases: List[str]
    docstring: Optional[str] = None
    methods: List[FunctionInfo]
    decorators: List[str] = []
    line_start: int
    line_end: int

class FileInfo(BaseModel):
    path: str
    language: Language
    size_bytes: int
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[str]
    module_docstring: Optional[str] = None

class FunctionDoc(BaseModel):
    function_name: str
    file: str
    parameters: List[ParameterInfo] = []
    returns: Optional[str] = None
    summary: str

class ModuleSummary(BaseModel):
    file: str
    purpose: str
    workflow: str = ""
    notes: str = ""

class RepositoryStructure(BaseModel):
    files: List[FileInfo]
    language_breakdown: dict = {}

class DocStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentationResult(BaseModel):
    id: UUID
    project_id: UUID
    commit_sha: str = ""
    status: DocStatus = DocStatus.PENDING
    readme_markdown: str = ""
    module_map: dict = {}
    function_docs: List[FunctionDoc] = []
    module_summaries: List[ModuleSummary] = []
    generated_at: Optional[datetime] = None
    error: Optional[str] = None

class DocumentationRequest(BaseModel):
    project_id: UUID
    repo_path: str
    branch: str = "main"
    commit_sha: str = ""
    user_id: UUID
    regenerate: bool = False

class DocumentationResponse(BaseModel):
    doc_id: UUID
    project_id: UUID
    status: DocStatus
    message: str    
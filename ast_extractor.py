"""
services/documentation/parser/ast_extractor.py

Extract structured metadata from Python source files using the stdlib `ast` module.
Produces FileInfo objects that feed the Intermediate Representation.
"""
from __future__ import annotations

import ast
import textwrap
from pathlib import Path

from models import (
    ClassInfo,
    FileInfo,
    FunctionInfo,
    Language,
    ParameterInfo,
)
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _annotation_to_str(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _default_to_str(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _extract_decorators(decorator_list: list[ast.expr]) -> list[str]:
    decorators = []
    for dec in decorator_list:
        try:
            decorators.append(ast.unparse(dec))
        except Exception:
            pass
    return decorators


def _extract_imports(tree: ast.Module) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}" if module else alias.name)
    return imports


# ── Function extractor ────────────────────────────────────────────────────────

def _extract_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    is_method: bool = False,
) -> FunctionInfo:
    params: list[ParameterInfo] = []
    args = node.args

    # Build default mapping (defaults align to the RIGHT of the args list)
    all_args = args.posonlyargs + args.args
    defaults_offset = len(all_args) - len(args.defaults)

    for i, arg in enumerate(all_args):
        if arg.arg == "self" or arg.arg == "cls":
            continue
        default_idx = i - defaults_offset
        default = (
            _default_to_str(args.defaults[default_idx])
            if default_idx >= 0
            else None
        )
        params.append(
            ParameterInfo(
                name=arg.arg,
                type_hint=_annotation_to_str(arg.annotation),
                default=default,
            )
        )

    # kwonly args
    for i, arg in enumerate(args.kwonlyargs):
        kw_default = args.kw_defaults[i] if i < len(args.kw_defaults) else None
        params.append(
            ParameterInfo(
                name=arg.arg,
                type_hint=_annotation_to_str(arg.annotation),
                default=_default_to_str(kw_default),
            )
        )

    return FunctionInfo(
        name=node.name,
        parameters=params,
        return_type=_annotation_to_str(node.returns),
        docstring=ast.get_docstring(node),
        decorators=_extract_decorators(node.decorator_list),
        line_start=node.lineno,
        line_end=node.end_lineno or node.lineno,
        is_async=isinstance(node, ast.AsyncFunctionDef),
        is_method=is_method,
    )


# ── Class extractor ───────────────────────────────────────────────────────────

def _extract_class(node: ast.ClassDef) -> ClassInfo:
    bases = []
    for base in node.bases:
        try:
            bases.append(ast.unparse(base))
        except Exception:
            pass

    methods: list[FunctionInfo] = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_extract_function(item, is_method=True))

    return ClassInfo(
        name=node.name,
        bases=bases,
        docstring=ast.get_docstring(node),
        methods=methods,
        decorators=_extract_decorators(node.decorator_list),
        line_start=node.lineno,
        line_end=node.end_lineno or node.lineno,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def extract_python_file(
    filepath: Path,
    repo_root: Path,
) -> FileInfo | None:
    """
    Parse *filepath* as Python source and return a FileInfo.
    Returns None if the file cannot be parsed (syntax errors, encoding issues).
    """
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        log.warning("file_read_error", path=str(filepath), error=str(exc))
        return None

    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as exc:
        log.warning("syntax_error", path=str(filepath), error=str(exc))
        return None

    relative_path = str(filepath.relative_to(repo_root))
    size_bytes = filepath.stat().st_size

    functions: list[FunctionInfo] = []
    classes: list[ClassInfo] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_extract_function(node))
        elif isinstance(node, ast.ClassDef):
            classes.append(_extract_class(node))

    return FileInfo(
        path=relative_path,
        language=Language.PYTHON,
        size_bytes=size_bytes,
        functions=functions,
        classes=classes,
        imports=_extract_imports(tree),
        module_docstring=ast.get_docstring(tree),
    )

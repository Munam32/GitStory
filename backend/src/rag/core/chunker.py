# core/chunker.py
# Migrated from tree_sitter_languages (abandoned, no Python 3.13 support)
# to tree_sitter_language_pack (maintained, downloads grammars on-demand)
from tree_sitter_language_pack import process, ProcessConfig, available_languages, get_language
from pathlib import Path


# ── Language config ──────────────────────────────────────
# Maps file extension → tree-sitter language name
EXTENSION_TO_LANGUAGE = {
    '.py':    'python',
    '.js':    'javascript',
    '.ts':    'typescript',
    '.jsx':   'javascript',
    '.tsx':   'typescript',
    '.java':  'java',
    '.cpp':   'cpp',
    '.c':     'c',
    '.cs':    'c_sharp',
    '.go':    'go',
    '.rs':    'rust',
    '.rb':    'ruby',
    '.php':   'php',
    '.swift': 'swift',
    '.kt':    'kotlin',
    '.scala': 'scala',
    '.r':     'r',
    '.lua':   'lua',
}

# Text-based formats — no AST needed, just line chunking
TEXT_EXTENSIONS = {'.md', '.txt', '.yaml', '.yml', '.json', '.toml', '.ini', '.env'}


# ── Core tree-sitter extractor (using tree_sitter_language_pack) ──
def chunk_with_treesitter(file_path: str, content: str, ts_lang: str) -> list:
    """
    Uses tree_sitter_language_pack's `process()` API to extract
    structural chunks (functions, classes, methods, etc.) from source code.
    Falls back to line-based chunking on any failure.
    """
    try:
        cfg = ProcessConfig(language=ts_lang)
        result = process(content, cfg)
    except Exception as e:
        print(f"[chunker] tree-sitter-language-pack failed for {ts_lang}: {e}")
        return chunk_by_lines(file_path, content)

    chunks = []
    lines = content.splitlines()

    # Extract structural items (functions, classes, methods, etc.)
    for item in result.structure:
        start_line = item.span.start_line       # 0-indexed
        end_line = item.span.end_line + 1       # make exclusive

        block = "\n".join(lines[start_line:end_line])

        # Skip tiny nodes — one-liners, empty declarations
        if len(block.strip()) < 40:
            continue

        chunks.append({
            "text": block,
            "file_path": file_path,
            "type": str(item.kind),
            "name": item.name or f"anonymous_{item.kind}",
            "start_line": start_line + 1,   # back to 1-indexed for humans
            "end_line": end_line,
        })

    # Always prepend module-level context (imports, constants)
    header = _extract_header(lines)
    if header:
        chunks.insert(0, {
            "text": header,
            "file_path": file_path,
            "type": "header",
            "name": "__imports__",
            "start_line": 1,
            "end_line": len(header.splitlines()),
        })

    return chunks if chunks else chunk_by_lines(file_path, content)


def _extract_header(lines: list, max_lines: int = 30) -> str:
    """First N lines of a file — captures imports and global constants."""
    header = "\n".join(lines[:max_lines])
    # Only return if there's actually something meaningful
    return header if len(header.strip()) > 20 else ""


# ── Fallback: line-based chunking ────────────────────────
def chunk_by_lines(file_path: str, content: str, chunk_size: int = 60, overlap: int = 10) -> list:
    """For markdown, JSON, YAML, or when tree-sitter fails."""
    lines = content.splitlines()
    chunks = []
    step = chunk_size - overlap

    for i in range(0, len(lines), step):
        block = "\n".join(lines[i:i + chunk_size])
        if block.strip():
            chunks.append({
                "text": block,
                "file_path": file_path,
                "type": "lines",
                "name": f"lines_{i+1}_{i+chunk_size}",
                "start_line": i + 1,
                "end_line": min(i + chunk_size, len(lines)),
            })
    return chunks


# ── Main entry point ─────────────────────────────────────
def chunk_file(file_path: str, content: str) -> list:
    """
    Call this from anywhere. Automatically picks the right strategy.
    """
    ext = Path(file_path).suffix.lower()

    # Known text formats — no AST
    if ext in TEXT_EXTENSIONS:
        return chunk_by_lines(file_path, content)

    # Known code language — use tree-sitter
    if ext in EXTENSION_TO_LANGUAGE:
        ts_lang = EXTENSION_TO_LANGUAGE[ext]
        return chunk_with_treesitter(file_path, content, ts_lang)

    # Unknown extension — try line chunking
    print(f"[chunker] Unknown extension {ext}, using line chunking for {file_path}")
    return chunk_by_lines(file_path, content)

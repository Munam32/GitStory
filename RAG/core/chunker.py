# core/chunker.py
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser
from pathlib import Path


# ── Language config ──────────────────────────────────────
# Maps file extension → (tree-sitter language name, meaningful node types)
# "meaningful node types" = the AST nodes we want to extract as chunks
LANGUAGE_CONFIG = {
    # Extension : (ts_language,  node_types_to_extract)
    '.py':   ('python',     ['function_definition', 'class_definition']),
    '.js':   ('javascript', ['function_declaration', 'class_declaration','arrow_function', 'method_definition']),
    '.ts':   ('typescript', ['function_declaration', 'class_declaration','arrow_function', 'method_definition']),
    '.jsx':  ('javascript', ['function_declaration', 'class_declaration','arrow_function', 'jsx_element']),
    '.tsx':  ('typescript', ['function_declaration', 'class_declaration','arrow_function', 'jsx_element']),
    '.java': ('java',       ['method_declaration', 'class_declaration','interface_declaration', 'constructor_declaration']),
    '.cpp':  ('cpp',        ['function_definition', 'class_specifier']),
    '.c':    ('c',          ['function_definition']),
    '.cs':   ('c_sharp',    ['method_declaration', 'class_declaration','constructor_declaration', 'interface_declaration']),
    '.go':   ('go',         ['function_declaration', 'method_declaration','type_declaration']),
    '.rs':   ('rust',       ['function_item', 'impl_item', 'struct_item','enum_item', 'trait_item']),
    '.rb':   ('ruby',       ['method', 'class', 'module']),
    '.php':  ('php',        ['function_definition', 'class_declaration','method_declaration']),
    '.swift':('swift',      ['function_declaration', 'class_declaration','struct_declaration', 'protocol_declaration']),
    '.kt':   ('kotlin',     ['function_declaration', 'class_declaration','object_declaration']),
    '.scala':('scala',      ['function_definition', 'class_definition','object_definition', 'trait_definition']),
    '.r':    ('r',          ['function_definition']),
    '.lua':  ('lua',        ['function_declaration', 'local_function']),
}

# Text-based formats — no AST needed, just line chunking
TEXT_EXTENSIONS = {'.md', '.txt', '.yaml', '.yml', '.json', '.toml', '.ini', '.env'}


# ── Core tree-sitter extractor ───────────────────────────
def chunk_with_treesitter(file_path: str, content: str,ts_lang: str, node_types: list) -> list:
    """
    Universal chunker. Works for any language tree-sitter supports.
    Walks the syntax tree and extracts meaningful nodes as chunks.
    """
    try:
        parser = get_parser(ts_lang)
    except Exception as e:
        print(f"[chunker] tree-sitter failed for {ts_lang}: {e}")
        return chunk_by_lines(file_path, content)

    # tree-sitter works on bytes, not strings
    content_bytes = content.encode('utf-8')
    tree = parser.parse(content_bytes)

    chunks = []
    lines = content.splitlines()

    def walk(node):
        """Recursively walk the syntax tree."""
        if node.type in node_types:
            start_line = node.start_point[0]    # (row, col) — 0 indexed
            end_line = node.end_point[0] + 1    # make it exclusive

            block = "\n".join(lines[start_line:end_line])

            # Skip tiny nodes — one-liners, empty declarations
            if len(block.strip()) < 40:
                # Still walk children — might have nested functions
                for child in node.children:
                    walk(child)
                return

            # Extract the name if possible
            name = _extract_name(node, content_bytes)

            chunks.append({
                "text": block,
                "file_path": file_path,
                "type": node.type,
                "name": name,
                "start_line": start_line + 1,   # back to 1-indexed for humans
                "end_line": end_line,
            })

            # Don't walk children of extracted nodes
            # (avoids double-extracting nested functions inside a class)
            return

        # Not a target node — keep walking down
        for child in node.children:
            walk(child)

    walk(tree.root_node)

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


def _extract_name(node, content_bytes: bytes) -> str:
    """
    Tries to find the name of a function/class node.
    tree-sitter puts the name in a child node called 'identifier' or 'name'.
    """
    for child in node.children:
        if child.type in ('identifier', 'name', 'type_identifier'):
            return content_bytes[child.start_byte:child.end_byte].decode('utf-8')
    return f"anonymous_{node.type}"


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
    if ext in LANGUAGE_CONFIG:
        ts_lang, node_types = LANGUAGE_CONFIG[ext]
        return chunk_with_treesitter(file_path, content, ts_lang, node_types)

    # Unknown extension — try line chunking
    print(f"[chunker] Unknown extension {ext}, using line chunking for {file_path}")
    return chunk_by_lines(file_path, content)


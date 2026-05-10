from pathlib import Path
from tree_sitter import Language, Parser
import tree_sitter_javascript as tsjs
import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
import tree_sitter_java as tsjava
import tree_sitter_c_sharp as tscs

from models import FileInfo, FunctionInfo, Language as LangEnum

# 1. The Language Registry
# Maps file extensions to their Tree-sitter Language object and specific syntax query.
LANGUAGE_REGISTRY = {
    ".js": {
        "lang": Language(tsjs.language()),
        "query": """
            (function_declaration name: (identifier) @func.name)
            (method_definition name: (property_identifier) @func.name)
        """
    },
    ".c": {
        "lang": Language(tsc.language()),
        "query": "(function_definition declarator: (function_declarator declarator: (identifier) @func.name))"
    },
    ".cpp": {
        "lang": Language(tscpp.language()),
        "query": """
            (function_definition declarator: (function_declarator declarator: (identifier) @func.name))
            (function_definition declarator: (function_declarator declarator: (field_identifier) @func.name))
        """
    },
    ".java": {
        "lang": Language(tsjava.language()),
        "query": "(method_declaration name: (identifier) @func.name)"
    },
    ".cs": {
        "lang": Language(tscs.language()),
        "query": "(method_declaration name: (identifier) @func.name)"
    }
}

def extract_with_treesitter(filepath: Path, repo_root: Path) -> FileInfo | None:
    """Universally extracts functions from any registered language."""
    ext = filepath.suffix.lower()
    if ext not in LANGUAGE_REGISTRY:
        return None

    config = LANGUAGE_REGISTRY[ext]
    
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    # Boot the parser for this specific language
    parser = Parser(config["lang"])
    tree = parser.parse(bytes(source, "utf8"))
    
    # Compile and run the specific query
    query = config["lang"].query(config["query"])
    matches = query.matches(tree.root_node)
    
    functions = []
    for _, captures in matches:
        for capture_name, nodes in captures.items():
            if capture_name == "func.name":
                for node in nodes:
                    functions.append(FunctionInfo(
                        name=node.text.decode("utf8"),
                        parameters=[], # Can be expanded later
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1
                    ))

    return FileInfo(
        path=str(filepath.relative_to(repo_root)),
        language=LangEnum.PYTHON, # Update your Enum in models.py to handle actual languages eventually
        size_bytes=filepath.stat().st_size,
        functions=functions,
        classes=[], 
        imports=[],
        module_docstring=None
    )
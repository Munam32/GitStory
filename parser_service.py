import os
from pathlib import Path
from uuid import UUID

from models import RepositoryStructure, FileInfo
from ast_extractor import extract_python_file
from tree_sitter_extractor import extract_with_treesitter

# Directories we never want to parse
IGNORED_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}

class ParserService:
    def parse(self, repo_path: str, project_id: UUID = None, branch: str = "main", commit_sha: str = "") -> RepositoryStructure:
        """
        Walks the repository directory, routes files to the correct parser 
        based on extension, and compiles the Intermediate Representation (IR).
        """
        root = Path(repo_path)
        parsed_files = []
        language_counts = {"python": 0}

        for current_root, dirs, files in os.walk(root):
            # Prune ignored directories so os.walk doesn't even enter them
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file in files:
                filepath = Path(current_root) / file
                ext = filepath.suffix.lower()

                result: FileInfo | None = None

                # Route to the correct parsing engine
                if ext == ".py":
                    result = extract_python_file(filepath, root)
                    if result: 
                        language_counts["python"] = language_counts.get("python", 0) + 1
                
                # Route ALL other supported extensions to the universal parser
                elif ext in [".js", ".c", ".cpp", ".java", ".cs"]:
                    result = extract_with_treesitter(filepath, root)
                    if result: 
                        lang_name = ext.replace(".", "")
                        language_counts[lang_name] = language_counts.get(lang_name, 0) + 1
                
                else:
                    language_counts["unsupported"] = language_counts.get("unsupported", 0) + 1

                if result:
                    parsed_files.append(result)

        return RepositoryStructure(
            files=parsed_files,
            language_breakdown=language_counts
        )
# pipelines/repo_importer.py
import git
import os
import shutil
from pathlib import Path
from core.file_filter import should_keep_file

def import_repo(repo_url: str, base_dir: str = "./repos") -> list:
    """
    Takes a GitHub URL, clones it, returns list of files ready for indexing.
    Returns: [{"file_path": str, "content": str, "size": int}]
    """
    
    # Extract repo name from URL
    # "https://github.com/user/myrepo" → "myrepo"
    repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
    clone_path = os.path.join(base_dir, repo_name)
    
    # If already cloned, skip (caching)
    if os.path.exists(clone_path):
        print(f"Repo already cloned at {clone_path}, using cached version.")
    else:
        print(f"Cloning {repo_url}...")
        git.Repo.clone_from(
            repo_url,
            clone_path,
            depth=1  # Shallow clone — only latest snapshot, no full history
# PyDriller handles history separately, so depth=1 is fine here
        )
        print("Clone done.")
    
    # Walk all files and collect
    files = []
    for file_path in Path(clone_path).rglob("*"):
        if not file_path.is_file():
            continue
        
        size = file_path.stat().st_size
        rel_path = str(file_path.relative_to(clone_path))  # e.g. "src/auth/jwt.py"
        
        if not should_keep_file(rel_path, size):
            continue
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            files.append({
                "file_path": rel_path,
                "content": content,
                "size": size
            })
        except Exception:
            continue  # Skip unreadable files silently
    
    print(f"Imported {len(files)} files from {repo_name}")
    return [files, clone_path]
    
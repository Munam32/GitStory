import os
from pipelines.importer import import_repo
from pipelines.history_indexer import index_commit_history
from core.summarizer import summarize_all_files
from core.mapper import generate_global_map
from core.chunker import chunk_file
from core.vector_store import GitStoryDB
from core.engine import GitStoryEngine

MAPS_DIR = "./project_maps"


def _repo_name_from_url(repo_url: str) -> str:
    """Extract a short, safe name from a GitHub URL."""
    return repo_url.rstrip('/').split('/')[-1].replace('.git', '')


def run_git_story_pipeline(repo_url: str, db_path: str = "./chroma_db",
                           maps_dir: str = MAPS_DIR) -> str:
    """
    Full RAG indexing pipeline for a single GitHub repository.
    Returns the repo_name on success so callers can reference it.
    """
    repo_name = _repo_name_from_url(repo_url)
    print(f"\n{'='*60}\nSTARTING GITSTORY PIPELINE for '{repo_name}'\n{'='*60}")

    # 1. Initialize per-repo Database
    db = GitStoryDB(db_path=db_path, repo_name=repo_name)

    # 2. Import and Filter Repo
    result = import_repo(repo_url)
    files, clone_path = result.files, result.clone_path

    if not files:
        print("No valid files found after filtering. Check file_filter.py.")
        return repo_name

    # 3. Summarize all files in parallel
    print(f"\nSummarizing {len(files)} files in parallel...")
    all_summaries = summarize_all_files(files)
    db.add_summaries(all_summaries)
    print(f"   {len(all_summaries)} summaries stored.")

    # 4. AST Chunk all files
    print(f"\nChunking {len(files)} files with tree-sitter...")
    for file_data in files:
        chunks = chunk_file(file_data['file_path'], file_data['content'])
        db.add_ast_chunks(chunks)

    # 5. Generate & Save per-repo Global Project Map
    print("\nGenerating Global Architect Map...")
    project_map = generate_global_map(all_summaries)

    os.makedirs(maps_dir, exist_ok=True)
    map_path = os.path.join(maps_dir, f"{repo_name}.json")
    with open(map_path, "w", encoding="utf-8") as f:
        f.write(project_map)
    print(f"   Project Map saved to {map_path}")

    # 6. Index commit history with PyDriller
    index_commit_history(clone_path, db)

    print(f"\n{'='*60}\nINDEXING COMPLETE for '{repo_name}'\n{'='*60}")
    return repo_name


if __name__ == "__main__":
    import sys
    target_repo = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/MSabihkhan/CV"
    name = run_git_story_pipeline(target_repo)

    # Optional smoke test
    engine = GitStoryEngine(repo_name=name)
    print("\nQUICK TEST: 'What is the main purpose of this repo?'")
    print(engine.ask("What is the main purpose of this repo?"))

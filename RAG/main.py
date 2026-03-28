import os
from pipelines.importer import import_repo
from core.summarizer import summarize_all_files
from core.mapper import generate_global_map
from core.chunker import chunk_file
from core.vector_store import GitStoryDB
from core.engine import GitStoryEngine 

def run_git_story_pipeline(repo_url):
    print(f"\n{'='*60}\n🎬 STARTING GITSTORY PIPELINE\n{'='*60}")
    
    # 1. Initialize Database
    db = GitStoryDB()
    # 2. Import and Filter Repo
    result = import_repo(repo_url)
    files, clone_path = result.files, result.clone_path
    
    if not files:
        print("❌ No valid files found after filtering. Check file_filter.py.")
        return

    # 3. Summarize all files in parallel
    print(f"\n🧠 Summarizing {len(files)} files in parallel...")
    all_summaries = summarize_all_files(files)
    db.add_summaries(all_summaries)
    print(f"   ✅ {len(all_summaries)} summaries stored.")

    # 4. AST Chunk all files
    print(f"\n🌳 Chunking {len(files)} files with tree-sitter...")
    for file_data in files:
        chunks = chunk_file(file_data['file_path'], file_data['content'])
        db.add_ast_chunks(chunks)

    # 5. Generate & Save Global Project Map
    print("\n🗺️ Generating Global Architect Map...")
    project_map = generate_global_map(all_summaries)
    
    with open("project_map.json", "w", encoding="utf-8") as f:
        f.write(project_map)
    print("   ✅ Project Map saved to project_map.json")

    print(f"\n{'='*60}\n✨ INDEXING COMPLETE\n{'='*60}")
    
    # Optional: Immediate Smoke Test Query
    engine = GitStoryEngine()
    print("\n🤔 QUICK TEST: 'What is the main purpose of this repo?'")
    print(engine.ask("What is the main purpose of this repo?"))

if __name__ == "__main__":
    # Test with a target repository
    target_repo = "https://github.com/MSabihkhan/CV" 
    run_git_story_pipeline(target_repo)
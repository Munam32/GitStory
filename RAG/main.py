import os
from pipelines.importer import import_repo
from core.summarizer import summarize_file
from core.mapper import generate_global_map
from core.chunker import chunk_file
from core.vector_store import GitStoryDB
# Assuming you named your query engine file core/query_engine.py
from core.engine import GitStoryEngine 

def run_git_story_pipeline(repo_url):
    print(f"\n{'='*60}\n🎬 STARTING GITSTORY PIPELINE\n{'='*60}")
    
    # 1. Initialize Database
    db = GitStoryDB()
    all_summaries = []

    # 2. Import and Filter Repo
    # Returns [files_list, clone_path]
    files, clone_path = import_repo(repo_url)
    
    if not files:
        print("❌ No valid files found after filtering. Check file_filter.py.")
        return

    # 3. Processing Loop: Summarize & AST Chunk
    print(f"\n🧠 Processing {len(files)} files...")
    for i, file_data in enumerate(files):
        path = file_data['file_path']
        content = file_data['content']
        
        print(f"   [{i+1}/{len(files)}] 📄 {path}")

        # A. Generate Summary
        summary_result = summarize_file(path, content)
        all_summaries.append(summary_result)
        
        # B. Store Summary in ChromaDB
        db.add_summaries([summary_result])

        # C. Generate AST Chunks (Tree-Sitter)
        chunks = chunk_file(path, content)
        
        # D. Store AST Chunks in ChromaDB
        db.add_ast_chunks(chunks)

    # 4. Generate & Save Global Project Map
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
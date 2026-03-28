# pipelines/history_indexer.py
from pydriller import Repository
from core.vector_store import GitStoryDB
from config import MAX_COMMITS, COMMIT_DIFF_MAX_CHARS


def index_commit_history(clone_path: str, db: GitStoryDB):
    """
    Walks the git history with PyDriller and indexes every
    commit+file-diff into the history_col ChromaDB collection.
    """
    print("\n📜 Indexing commit history with PyDriller...")

    records = []
    commit_count = 0

    for commit in Repository(clone_path).traverse_commits():
        if commit_count >= MAX_COMMITS:
            print(f"   ⚠️  Reached MAX_COMMITS limit ({MAX_COMMITS}), stopping.")
            break

        for mod in commit.modified_files:
            if not mod.diff:
                continue

            diff_text = mod.diff[:COMMIT_DIFF_MAX_CHARS]

            document = (
                f"COMMIT: {commit.msg.strip()}\n"
                f"AUTHOR: {commit.author.name}\n"
                f"DATE: {commit.author_date.strftime('%Y-%m-%d')}\n"
                f"FILE: {mod.filename}\n"
                f"DIFF:\n{diff_text}"
            )

            records.append({
                "id": f"{commit.hash[:8]}_{mod.filename}",
                "document": document,
                "metadata": {
                    "hash":          commit.hash[:8],
                    "author":        commit.author.name,
                    "date":          commit.author_date.strftime("%Y-%m-%d"),
                    "file":          mod.filename,
                    "lines_added":   mod.added_lines,
                    "lines_deleted": mod.deleted_lines,
                    "commit_msg":    commit.msg.strip()[:200],
                }
            })

        commit_count += 1

    db.add_commit_history(records)
    print(f"   ✅ Indexed {len(records)} file-change records from {commit_count} commits.")
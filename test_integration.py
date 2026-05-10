from uuid import uuid4
from datetime import datetime
from models import DocumentationResult, DocStatus

# --- MOCK REPOSITORY (Handles REQ-AD-05 & 07) ---
class MockDocumentationRepository:
    def __init__(self):
        self.db = {} # Simulating Supabase table

    def upsert(self, result: DocumentationResult):
        self.db[result.project_id] = result
        print(f"  [DB] Upserted doc record for project: {result.project_id}")
        print(f"  [DB] Status: {result.status.value.upper()} | Commit: {result.commit_sha}")

    def get_latest(self, project_id):
        return self.db.get(project_id)

# --- MOCK EXPORTER (Handles REQ-AD-06) ---
class MockExportService:
    def export_readme(self, result: DocumentationResult, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result.readme_markdown)
        print(f"  [Export] Successfully downloaded README to: {filepath}")


def test_final_requirements():
    print("Testing REQ-AD-05, 06, & 07...\n")
    repo = MockDocumentationRepository()
    exporter = MockExportService()

    # Shared project ID for the lifecycle
    project_id = uuid4()

    # 1. Simulate First Generation (REQ-AD-05)
    print("--- Testing REQ-AD-05 (Supabase Storage) ---")
    initial_result = DocumentationResult(
        id=uuid4(),
        project_id=project_id,
        commit_sha="commit-a1b2c3d",
        status=DocStatus.COMPLETED,
        readme_markdown="# TestProject v1\n\nInitial generated documentation.",
        generated_at=datetime.now()
    )
    repo.upsert(initial_result) 

    # 2. Simulate User Exporting File (REQ-AD-06)
    print("\n--- Testing REQ-AD-06 (Export .md File) ---")
    saved_result = repo.get_latest(project_id)
    exporter.export_readme(saved_result, "EXPORTED_README.md") 

    # 3. Simulate Repo Re-sync & Regeneration (REQ-AD-07)
    print("\n--- Testing REQ-AD-07 (Regeneration on Re-sync) ---")
    print("  [Webhook] Detected new commit on branch 'main'...")
    regenerated_result = DocumentationResult(
        id=uuid4(),
        project_id=project_id,
        commit_sha="commit-e4f5g6h", # New commit detected
        status=DocStatus.COMPLETED,
        readme_markdown="# TestProject v2\n\nRegenerated documentation after new code sync.",
        generated_at=datetime.now()
    )
    repo.upsert(regenerated_result) 
    
    print("\n  [Export] Exporting updated README to verify...")
    exporter.export_readme(repo.get_latest(project_id), "EXPORTED_README_V2.md")

if __name__ == "__main__":
    test_final_requirements()
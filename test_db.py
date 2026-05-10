import asyncio
from uuid import uuid4
from datetime import datetime, timezone
from models import DocumentationResult, DocStatus
from documentation_repository import DocumentationRepository

async def test_supabase():
    print("Testing Supabase Connection (REQ-AD-05)...")
    repo = DocumentationRepository()
    
    # 1. Create a dummy result
    project_id = uuid4()
    doc_id = uuid4()
    
    dummy_doc = DocumentationResult(
        id=doc_id,
        project_id=project_id,
        commit_sha="test-commit-123",
        status=DocStatus.COMPLETED,
        readme_markdown="# Database Test\nIt works!",
        generated_at=datetime.now(timezone.utc)
    )
    
    # 2. Insert into Supabase
    try:
        print(f"Upserting document {doc_id}...")
        await repo.upsert(dummy_doc)
        print("✅ Upsert successful.")
        
        # 3. Retrieve from Supabase
        print("Retrieving from database...")
        fetched = await repo.get_by_id(doc_id)
        
        if fetched and fetched.id == doc_id:
            print(f"✅ Fetch successful! Retrieved project ID: {fetched.project_id}")
            print(f"Readme preview: {fetched.readme_markdown}")
        else:
            print("❌ Fetch failed or ID mismatch.")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    asyncio.run(test_supabase())
from uuid import uuid4
from parser_service import ParserService

def test_router():
    print("Testing ParserService (The Polyglot Router)...")
    
    svc = ParserService()
    
    # Point the service at the current directory (".")
    ir = svc.parse(repo_path=".", project_id=uuid4())
    
    print("\n✅ PASS: Repository parsed successfully.")
    print("\n--- Language Breakdown ---")
    for lang, count in ir.language_breakdown.items():
        print(f"  {lang.capitalize()}: {count} files")
        
    print(f"\nTotal parsed files added to IR: {len(ir.files)}")
    
    # Let's prove it captured both Python and JS
    print("\n--- Parsed Files Preview ---")
    for file in ir.files:
        print(f"  - {file.path} ({len(file.functions)} functions)")

if __name__ == "__main__":
    test_router()
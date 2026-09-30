import json
from pathlib import Path
from src.docgen.ast_extractor import extract_python_file

DOCGEN_DIR = Path(__file__).resolve().parents[1] / "src" / "docgen"

def test_req_ad_01():
    print("Testing REQ-AD-01: AST Parsing...")
    
    # We will test the parser by having it parse its own code
    target_file = DOCGEN_DIR / "ast_extractor.py"
    repo_root = DOCGEN_DIR
    
    result = extract_python_file(target_file, repo_root)
    
    if result:
        print("\n✅ REQ-AD-01 PASS: File parsed successfully.")
        print(f"File Path: {result.path}")
        print(f"Total Functions Found: {len(result.functions)}")
        
        # Print a sample of the extracted data
        print("\n--- Extracted Data Preview ---")
        print(result.model_dump_json(indent=2))
    else:
        print("\n❌ REQ-AD-01 FAIL: Parser returned None.")

if __name__ == "__main__":
    test_req_ad_01()
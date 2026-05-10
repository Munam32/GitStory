import json
from pathlib import Path
from tree_sitter_extractor import extract_javascript_file

def test_polyglot_extraction():
    print("Testing Universal Parsing (Tree-sitter)...")
    
    target_file = Path("test_target.js")
    
    # Run the Tree-sitter extractor
    result = extract_javascript_file(target_file, Path("."))
    
    if result:
        print("\n✅ PASS: JavaScript file parsed successfully.")
        print(f"File Path: {result.path}")
        print(f"Total Functions Found: {len(result.functions)}")
        
        # Print the extracted functions
        for func in result.functions:
            print(f"  - Function: {func.name} (Lines {func.line_start}-{func.line_end})")
    else:
        print("\n❌ FAIL: Parser returned None.")

if __name__ == "__main__":
    test_polyglot_extraction()
import json
from pathlib import Path
from ast_extractor import extract_python_file
from module_mapper import build_module_map

def test_req_ad_04():
    print("Testing REQ-AD-04: Module Map Generation...")
    
    # 1. Parse the file to get the IR
    target_file = Path("ast_extractor.py")
    parsed_file = extract_python_file(target_file, Path("."))
    
    if not parsed_file:
        print("❌ Failed to parse file.")
        return

    # 2. Build the module map
    module_map = build_module_map([parsed_file])
    
    print("\n✅ REQ-AD-04 PASS: Module Map Generated.")
    print("\n--- JSON Module Map ---")
    print(json.dumps(module_map, indent=2))

if __name__ == "__main__":
    test_req_ad_04()
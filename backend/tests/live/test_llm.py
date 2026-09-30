import asyncio
from pathlib import Path
from src.docgen.ast_extractor import extract_python_file
from src.docgen.llm_doc_generator import LLMDocGenerator
from src.docgen.models import RepositoryStructure

DOCGEN_DIR = Path(__file__).resolve().parents[2] / "src" / "docgen"

async def test_req_ad_02_and_03():
    print("Testing REQ-AD-02 & 03: LLM Generation...")
    
    # 1. Get the IR (Intermediate Representation) from the parser
    target_file = DOCGEN_DIR / "ast_extractor.py"
    parsed_file = extract_python_file(target_file, DOCGEN_DIR)
    
    if not parsed_file:
        print("Failed to parse file.")
        return

    ir = RepositoryStructure(
        files=[parsed_file],
        language_breakdown={"python": 1}
    )

    # 2. Initialize the Generator
    generator = LLMDocGenerator()

    # 3. Test REQ-AD-02: README
    print("\n--- Generating README (REQ-AD-02) ---")
    readme = await generator.generate_readme(ir, "TestProject")
    print(readme)

    # 4. Test REQ-AD-03: Function Docs & Module Summaries
    print("\n--- Generating Function Docs (REQ-AD-03) ---")
    summaries = await generator.generate_module_summaries(ir.files)
    function_docs = await generator.generate_function_docs(ir.files)

    for summary in summaries:
        print(summary.model_dump_json(indent=2))
        
    for doc in function_docs:
        print(doc.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(test_req_ad_02_and_03())
import json

def build_readme_prompt(ir, project_name: str) -> str:
    return (
        f"Write a comprehensive README.md for a project named '{project_name}'.\n"
        f"The project has the following file structure and functions:\n"
        f"{json.dumps(ir.model_dump(), indent=2)}\n\n"
        "Include an Overview, Project Structure, and a brief description of the core files."
    )

def build_module_summary_prompt(file_info) -> str:
    return (
        f"Analyze this file: {file_info.path}\n"
        f"Functions included: {[f.name for f in file_info.functions]}\n\n"
        "Return a JSON object with exactly these keys: "
        "'purpose' (string), 'workflow' (string), 'notes' (string)."
    )

def build_function_doc_prompt(file_info) -> str:
    funcs = [{"name": f.name, "params": [p.name for p in f.parameters]} for f in file_info.functions]
    return (
        f"Document the functions in this file: {file_info.path}\n"
        f"Functions to document: {json.dumps(funcs)}\n\n"
        "Return a JSON array of objects. Each object must have exactly these keys: "
        "'function_name' (string), 'file' (string), 'returns' (string), 'summary' (string)."
    )
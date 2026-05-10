from typing import List
from models import FileInfo

def build_module_map(files: List[FileInfo]) -> dict:
    """
    Constructs a JSON-serializable hierarchical map of the codebase.
    """
    module_map = {}
    for file in files:
        # Split path to handle nested directories if we had them
        parts = file.path.split('/')
        current_level = module_map
        
        # Traverse/build the directory structure
        for part in parts[:-1]:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
            
        # Add file details at the leaf node
        filename = parts[-1]
        current_level[filename] = {
            "language": file.language.value,
            "functions": [f.name for f in file.functions],
            "classes": [c.name for c in file.classes]
        }
        
    return module_map
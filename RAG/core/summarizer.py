import requests
import json
import os
from dotenv import load_dotenv
from config import MODEL
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = MODEL

SUMMARY_PROMPT = """You are analyzing source code. Given the file path and content, 
write a concise 2-3 sentence summary covering:
1. What this file does
2. Key functions/classes it contains
3. What other parts of the system it likely connects to

Be specific. Mention actual function names and concepts. Do NOT be vague.

File: {file_path}
Content:
{content}

Summary:"""

def detect_language(file_path: str) -> str:
    """Simple extension-based language detection."""
    ext = os.path.splitext(file_path)[1].lower()
    mapping = {
    # --- Web & Frontend ---
    '.py': 'Python', 
    '.js': 'JavaScript', 
    '.ts': 'TypeScript', 
    '.tsx': 'React (TypeScript)', 
    '.jsx': 'React (JavaScript)', 
    '.html': 'HTML',
    '.css': 'CSS', 
    '.scss': 'Sass/SCSS',
    '.vue': 'Vue.js',
    '.svelte': 'Svelte',

    # --- Systems & Backend ---
    '.go': 'Go (Golang)',
    '.rs': 'Rust',
    '.java': 'Java',
    '.kt': 'Kotlin',
    '.cs': 'C#',
    '.cpp': 'C++',
    '.c': 'C',
    '.h': 'C/C++ Header',
    '.hpp': 'C++ Header',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.scala': 'Scala',

    # --- Mobile ---
    '.swift': 'Swift',
    '.m': 'Objective-C',
    '.dart': 'Dart (Flutter)',

    # --- Data & Config ---
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.toml': 'TOML',
    '.sql': 'SQL Database',
    '.xml': 'XML',
    '.csv': 'CSV Data',

    # --- Documentation & Shell ---
    '.md': 'Markdown',
    '.txt': 'Plain Text',
    '.sh': 'Shell Script (Bash)',
    '.zsh': 'Zsh Script',
    '.bat': 'Batch Script',
    '.ps1': 'PowerShell',
    
    # --- DevOps & Infrastructure ---
    '.dockerfile': 'Docker Configuration',
    '.tf': 'Terraform (HCL)',
    '.proto': 'Protocol Buffers'
}
    return mapping.get(ext, 'Unknown')

def summarize_file(file_path: str, content: str) -> dict:
    # Nemotron can handle a lot! Let's increase the limit to 15,000 chars (~4k tokens)
    # This ensures we don't miss the middle/end of important files.
    truncated = content[:15000] if len(content) > 15000 else content
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": MODEL_NAME,
                "messages": [
                    {"role": "user", "content": SUMMARY_PROMPT.format(file_path=file_path, content=truncated)}
                ],
                "temperature": 0.3 # Lower temperature = more consistent summaries
            })
        )
        
        result = response.json()
        # OpenRouter's response structure
        summary = result['choices'][0]['message']['content'].strip()
        
    except Exception as e:
        print(f"Error summarizing {file_path}: {e}")
        # Fallback: Just take the first bit of the file
        summary = f"Source file for {file_path}. Starts with: " + truncated[:150].replace('\n', ' ')
        
    return {
        "file_path": file_path,
        "summary": summary,
        "language": detect_language(file_path),
        "size_chars": len(content)
    }
    

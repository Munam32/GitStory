import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from config import MODEL, API_RETRY_ATTEMPTS, API_RETRY_WAIT_MIN, API_RETRY_WAIT_MAX, MAX_SUMMARY_WORKERS

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

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
    
    
@retry(stop=stop_after_attempt(API_RETRY_ATTEMPTS), wait=wait_exponential(min=API_RETRY_WAIT_MIN, max=API_RETRY_WAIT_MAX))
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
                "model": MODEL,
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
    
    
def summarize_all_files(files: list) -> list:
    """Summarizes all files in parallel using a thread pool."""
    results = []
    with ThreadPoolExecutor(max_workers=MAX_SUMMARY_WORKERS) as pool:
        futures = {
            pool.submit(summarize_file, f['file_path'], f['content']): f
            for f in files
        }
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                f = futures[future]
                print(f"❌ Failed to summarize {f['file_path']}: {e}")
    return results
    
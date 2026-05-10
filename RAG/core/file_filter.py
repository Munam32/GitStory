import os

# 1. Folders we NEVER want to look inside
IGNORED_DIRS = {
    '.git', '.github', '.vscode', '.idea', '__pycache__', 
    'node_modules', 'venv', '.venv', 'env', 'dist', 'build', 
    'target', 'bin', 'obj', '.next', '.cache'
}

# 2. File extensions that are definitely NOT source code (Binaries/Media)
IGNORED_EXTENSIONS = {
    # Images/Media
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.mp3', '.mp4', '.pdf', '.zip', '.tar', '.gz',
    # Compiled Code
    '.pyc', '.exe', '.dll', '.so', '.o', '.a', '.class', '.jar',
    # Lock files (usually huge and unhelpful for a "story")
    '.lock'
}

IGNORED_FILENAMES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml'
}
# 3. Maximum size (500 KB) - Large files are usually data, not logic
MAX_FILE_SIZE = 500 * 1024 

def should_keep_file(file_path: str, size: int) -> bool:
    """
    Decides if a file is worth reading and indexing.
    Returns True if it's a valid source file, False otherwise.
    """
    
    # Convert to lowercase and use forward slashes for consistent checking
    norm_path = file_path.replace('\\', '/').lower()
    parts = norm_path.split('/')

    # Rule 1: Check if the file is too big
    if size > MAX_FILE_SIZE:
        return False

    # Rule 2: Check if any part of the path is in an ignored directory
    # (e.g., "src/node_modules/react/index.js" -> False)
    if any(dir_name in parts for dir_name in IGNORED_DIRS):
        return False

    # Rule 3: Ignore hidden files (starting with .) 
    # except for important ones like .env or .gitignore if you want them
    filename = parts[-1]
    if filename.startswith('.') and filename not in ['.env', '.gitignore']:
        return False
    if filename in IGNORED_FILENAMES:
        return False
    # Rule 4: Check the extension
    _, ext = os.path.splitext(norm_path)
    if ext in IGNORED_EXTENSIONS:
        return False

    # If it passed all tests, it's a keeper!
    return True
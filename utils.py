import re

def parse_repo_url(repo_url: str):
    """
    Parses a GitHub URL to extract the base repository URL and the branch (if any).
    Example: https://github.com/user/repo/tree/main -> (https://github.com/user/repo, main)
    """
    base_url = repo_url
    branch = None
    
    # Extract branch from GitHub tree URL (e.g., https://github.com/user/repo/tree/branch-name)
    match = re.match(r"(https?://github\.com/[^/]+/[^/]+)/tree/(.+)", repo_url)
    if match:
        base_url = match.group(1)
        branch = match.group(2)
    
    # Ensure base_url ends with .git for better compatibility with Pydriller
    if base_url.startswith("https://github.com") and not base_url.endswith(".git"):
        base_url += ".git"
    
    return base_url, branch

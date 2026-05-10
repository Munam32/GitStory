import os
from pydriller import Repository
from utils import parse_repo_url

def extract_repo_data(repo_url: str, max_commits: int = 100):
    print(f"--- DEBUG: Starting extract_repo_data for {repo_url} (max_commits={max_commits}) ---")
    commits_data = []
    try:
        base_url, branch = parse_repo_url(repo_url)
        if branch:
            print(f"--- DEBUG: Detected branch '{branch}' for repo {base_url} ---")
        
        kwargs = {'order': 'reverse'}
        if branch:
            kwargs['only_in_branch'] = branch

        print(f"--- DEBUG: Initializing Repository traversal... ---")
        try:
            for commit in Repository(base_url, **kwargs).traverse_commits():
                if len(commits_data) >= max_commits:
                    print(f"--- DEBUG: Reached max_commits limit ({max_commits}) ---")
                    break
                
                commits_data.append({
                    "hash": commit.hash,
                    "msg": commit.msg,
                    "author": commit.author.name,
                    "date": commit.author_date.isoformat(),
                    "insertions": commit.insertions,
                    "deletions": commit.deletions,
                    "files_changed": len(commit.modified_files),
                })
        except Exception as branch_err:
            if branch:
                print(f"--- DEBUG: Branch traversal failed for '{branch}', falling back to default branch: {branch_err}")
                # Fallback: Try without branch restriction
                kwargs.pop('only_in_branch', None)
                for commit in Repository(base_url, **kwargs).traverse_commits():
                    if len(commits_data) >= max_commits: break
                    commits_data.append({
                        "hash": commit.hash,
                        "msg": commit.msg,
                        "author": commit.author.name,
                        "date": commit.author_date.isoformat(),
                        "insertions": commit.insertions,
                        "deletions": commit.deletions,
                        "files_changed": len(commit.modified_files),
                    })
            else:
                raise branch_err
        
        print(f"--- DEBUG: Extracted {len(commits_data)} commits. Reversing for chronological order. ---")
        return commits_data[::-1]
    except Exception as e:
        print(f"--- DEBUG ERROR: Error extracting repo data: {e} ---")
        return []

def get_file_history(repo_url: str, file_path: str):
    print(f"Extracting history for {file_path} from {repo_url}...")
    history = []
    try:
        base_url, branch = parse_repo_url(repo_url)
        
        kwargs = {'filepath': file_path, 'order': 'reverse'}
        if branch:
            kwargs['only_in_branch'] = branch

        def traverse_history():
            for commit in Repository(base_url, **kwargs).traverse_commits():
                history.append({
                    "hash": commit.hash,
                    "msg": commit.msg,
                    "author": commit.author.name,
                    "date": commit.author_date.isoformat(),
                    "insertions": commit.insertions,
                    "deletions": commit.deletions
                })
                if len(history) >= 50: # Limit to 50 commits
                    break

        try:
            traverse_history()
        except Exception as branch_err:
            if branch:
                print(f"--- DEBUG: File history branch traversal failed for '{branch}', falling back: {branch_err}")
                kwargs.pop('only_in_branch', None)
                traverse_history()
            else:
                raise branch_err
        
        return history
    except Exception as e:
        print(f"Error extracting file history: {e}")
        return []

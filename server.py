from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from github import Github
from pydriller import Repository

app = FastAPI()

# Middleware to allow Next.js(frontend) to talk to Python(backed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- DATA MODELS -----------------
class RepoListRequest(BaseModel):
    token: str

class AnalyzeRequest(BaseModel):
    repo_target: str       # e.g., "username/repo" or full URL
    token: str = None      # Optional, only needed for private
    is_private: bool = False




# ----------------- endpoints -----------------

@app.post("/get-repos")
def get_user_repos(req: RepoListRequest):
    """Fetches all repositories for the logged-in user."""
    try:
        g = Github(req.token)
        repos = []
        # Get all repos the user has access to
        for repo in g.get_user().get_repos():
            repos.append({"name": repo.full_name, "private": repo.private})
        return {"status": "Success", "repos": repos}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analyze")
def analyze_repo(req: AnalyzeRequest):
    """Mines both PyGithub stats and PyDriller history."""
    
    # Clean up the input to just "owner/repo"
    target_name = req.repo_target.replace("https://github.com/", "").strip()
    
    # Build the URL for PyDriller
    if req.is_private and req.token:
        # Sneak the token into the URL for private cloning!
        clone_url = f"https://oauth2:{req.token}@github.com/{target_name}.git"
        g = Github(req.token)
    else:
        clone_url = f"https://github.com/{target_name}.git"
        g = Github() # Anonymous access for public

    try:
        # --- 1. PYGITHUB EXTRACTION ---
        repo = g.get_repo(target_name)
        languages = repo.get_languages()
        
        pulls = repo.get_pulls(state='closed')
        # --- 1. PYGITHUB EXTRACTION ---
        repo = g.get_repo(target_name)
        languages = repo.get_languages()
        
        pulls = repo.get_pulls(state='closed')
        recent_prs = []
        
        # Safely grab up to 5 PRs, but don't crash if there are 0!
        for pr in pulls:
            recent_prs.append({"number": pr.number, "title": pr.title})
            if len(recent_prs) >= 5:
                break

        # --- 2. PYDRILLER EXTRACTION ---
        user_commits = {}
        file_hotzones = {}
        commit_history = [] # NEW: We will store the actual story here!
        commit_count = 0
        
        for commit in Repository(clone_url).traverse_commits():
            if commit_count >= 15: 
                break
            
            author = commit.author.name
            user_commits[author] = user_commits.get(author, 0) + 1
            
            # NEW: Save the message, date, and hash for the AI and timeline charts!
            commit_history.append({
                "hash": commit.hash,
                "author": author,
                "date": commit.committer_date.isoformat(),
                "message": commit.msg
            })
            
            for modified_file in commit.modified_files:
                filename = modified_file.filename
                file_hotzones[filename] = file_hotzones.get(filename, 0) + 1
            
            commit_count += 1

        # Return everything as a massive dictionary to Next.js
        return {
            "status": "Success",
            "repo_analyzed": target_name,
            "is_private": req.is_private,
            "data": {
                "languages": languages,
                "recent_prs": recent_prs,
                "top_contributors": user_commits,
                "file_hotzones": file_hotzones,
                "recent_commits": commit_history # NEW: Added to the final payload!
            }
        }   

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
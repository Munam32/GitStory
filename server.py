import sys
import os
import uuid
import json

# Make the RAG package importable
sys.path.append(os.path.join(os.path.dirname(__file__), "RAG"))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from github import Github
from pydriller import Repository

from RAG.core.engine import GitStoryEngine
from RAG.main import run_git_story_pipeline, _repo_name_from_url

# ─── Paths (relative to this file's directory) ───────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
CHROMA_PATH = os.path.join(BASE_DIR, "RAG", "chroma_db")
MAPS_DIR    = os.path.join(BASE_DIR, "RAG", "project_maps")
REPOS_DIR   = os.path.join(BASE_DIR, "RAG", "repos")

# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(title="GitStory API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-memory stores ────────────────────────────────────────────────────────
# job_id → {"status": "pending|running|done|error", "repo_name": str, "error": str|None}
_index_jobs: dict[str, dict] = {}

# repo_name → GitStoryEngine (cached per repo to preserve conversation history)
_engines: dict[str, GitStoryEngine] = {}


def _get_engine(repo_name: str) -> GitStoryEngine:
    """Return a cached engine for a repo, creating it on first access."""
    if repo_name not in _engines:
        _engines[repo_name] = GitStoryEngine(
            repo_name=repo_name,
            db_path=CHROMA_PATH,
            maps_dir=MAPS_DIR,
        )
    return _engines[repo_name]


# ─── Data Models ─────────────────────────────────────────────────────────────

class RepoListRequest(BaseModel):
    token: str

class AnalyzeRequest(BaseModel):
    repo_target: str        # "owner/repo" or full GitHub URL
    token: str | None = None
    is_private: bool = False

class IndexRequest(BaseModel):
    repo_url: str           # Full GitHub URL, e.g. https://github.com/user/repo
    token: str | None = None
    is_private: bool = False

class ChatRequest(BaseModel):
    message: str
    repo_name: str          # Which indexed repo to query

class ResetRequest(BaseModel):
    repo_name: str


# ─── Background task ─────────────────────────────────────────────────────────

def _run_indexing(job_id: str, repo_url: str, token: str | None, is_private: bool):
    """Runs in a background thread; updates _index_jobs when done."""
    _index_jobs[job_id]["status"] = "running"
    try:
        # Inject token into URL for private repos
        if is_private and token:
            # e.g. https://oauth2:<token>@github.com/owner/repo
            path = repo_url.replace("https://github.com/", "")
            cloneable_url = f"https://oauth2:{token}@github.com/{path}"
        else:
            cloneable_url = repo_url

        repo_name = run_git_story_pipeline(
            repo_url=cloneable_url,
            db_path=CHROMA_PATH,
            maps_dir=MAPS_DIR,
        )
        _index_jobs[job_id]["status"] = "done"
        _index_jobs[job_id]["repo_name"] = repo_name

        # Invalidate cached engine so it picks up the fresh index & project map
        _engines.pop(repo_name, None)

    except Exception as e:
        _index_jobs[job_id]["status"] = "error"
        _index_jobs[job_id]["error"] = str(e)


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/")
def health():
    return {"status": "GitStory API is running", "version": "2.0.0"}


@app.post("/get-repos")
def get_user_repos(req: RepoListRequest):
    """Fetches all repositories visible to the authenticated GitHub user."""
    try:
        g = Github(req.token)
        repos = [
            {"name": r.full_name, "private": r.private}
            for r in g.get_user().get_repos()
        ]
        return {"status": "Success", "repos": repos}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/analyze")
def analyze_repo(req: AnalyzeRequest):
    """
    Mines surface-level metadata from a GitHub repo using PyGithub + PyDriller.
    Does NOT trigger the full RAG indexing pipeline — use /index-repo for that.
    """
    target_name = req.repo_target.replace("https://github.com/", "").strip().rstrip("/")

    if req.is_private and req.token:
        clone_url = f"https://oauth2:{req.token}@github.com/{target_name}.git"
        g = Github(req.token)
    else:
        clone_url = f"https://github.com/{target_name}.git"
        g = Github()

    try:
        # ── PyGithub metadata ──────────────────────────────────────────
        repo = g.get_repo(target_name)
        languages = repo.get_languages()

        recent_prs = []
        for pr in repo.get_pulls(state='closed'):
            recent_prs.append({"number": pr.number, "title": pr.title})
            if len(recent_prs) >= 5:
                break

        # ── PyDriller commit history ───────────────────────────────────
        user_commits: dict[str, int] = {}
        file_hotzones: dict[str, int] = {}
        commit_history = []
        commit_count = 0

        for commit in Repository(clone_url).traverse_commits():
            if commit_count >= 15:
                break
            author = commit.author.name
            user_commits[author] = user_commits.get(author, 0) + 1
            commit_history.append({
                "hash":    commit.hash,
                "author":  author,
                "date":    commit.committer_date.isoformat(),
                "message": commit.msg,
            })
            for mf in commit.modified_files:
                file_hotzones[mf.filename] = file_hotzones.get(mf.filename, 0) + 1
            commit_count += 1

        return {
            "status": "Success",
            "repo_analyzed": target_name,
            "is_private": req.is_private,
            "data": {
                "languages":       languages,
                "recent_prs":      recent_prs,
                "top_contributors": user_commits,
                "file_hotzones":   file_hotzones,
                "recent_commits":  commit_history,
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/index-repo")
def index_repo(req: IndexRequest, background_tasks: BackgroundTasks):
    """
    Kicks off the full RAG indexing pipeline for a GitHub repo in the background.
    Returns a job_id you can poll with GET /index-repo/status/{job_id}.
    """
    job_id = str(uuid.uuid4())
    repo_name = _repo_name_from_url(req.repo_url)

    _index_jobs[job_id] = {
        "status":    "pending",
        "repo_name": repo_name,
        "repo_url":  req.repo_url,
        "error":     None,
    }

    background_tasks.add_task(
        _run_indexing, job_id, req.repo_url, req.token, req.is_private
    )

    return {
        "status":    "accepted",
        "job_id":    job_id,
        "repo_name": repo_name,
        "message":   f"Indexing started for '{repo_name}'. Poll /index-repo/status/{job_id} for progress.",
    }


@app.get("/index-repo/status/{job_id}")
def index_status(job_id: str):
    """Returns the current status of an indexing job."""
    job = _index_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return {"job_id": job_id, **job}


@app.get("/indexed-repos")
def list_indexed_repos():
    """
    Returns all repos that have been successfully indexed (have a project map file).
    """
    repos = []
    if os.path.isdir(MAPS_DIR):
        for fname in os.listdir(MAPS_DIR):
            if fname.endswith(".json"):
                repos.append(fname[:-5])  # strip .json
    return {"status": "Success", "repos": repos}


@app.post("/chat")
async def chat_with_repo(req: ChatRequest):
    """
    Streams the AI response for a question about an indexed repo.
    Response is Server-Sent Events: each event is JSON {"token": "..."}.
    A final "data: [DONE]" signals completion.
    """
    # Validate the repo is indexed
    map_path = os.path.join(MAPS_DIR, f"{req.repo_name}.json")
    if not os.path.exists(map_path):
        raise HTTPException(
            status_code=404,
            detail=f"Repo '{req.repo_name}' is not indexed yet. Run POST /index-repo first."
        )

    engine = _get_engine(req.repo_name)
    return StreamingResponse(
        engine.ask_stream(req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "http://localhost:3000",
        }
    )


@app.post("/chat/reset")
def reset_chat_history(req: ResetRequest):
    """Clears conversation memory for a specific repo's engine."""
    engine = _engines.get(req.repo_name)
    if engine:
        engine.reset_history()
    return {"status": "History cleared", "repo_name": req.repo_name}

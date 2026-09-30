from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import modules
from timeline import extract_repo_data, get_file_history
from narration import NarrationGenerator
from heatmap import get_churn_data, generate_plotly_heatmap
from code_review import CodeReviewer

app = FastAPI(title="GitStory Central API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize generators
narration_gen = NarrationGenerator()
reviewer = CodeReviewer()

class ReviewRequest(BaseModel):
    repo_url: str
    commit_count: int = 1
    github_token: str

@app.get("/api/timeline")
async def get_timeline(repo_url: str = Query(..., description="GitHub Repository URL")):
    """Extracts commit history and generates a narrated timeline."""
    commits = extract_repo_data(repo_url)
    if not commits:
        raise HTTPException(status_code=400, detail="Could not extract data from repository.")
    
    narration = narration_gen.generate_narration(commits)
    return {
        "narration": narration,
        "commits": commits
    }

@app.get("/api/hotzone")
async def get_hotzone(repo_url: str = Query(..., description="GitHub Repository URL")):
    """Returns file churn data for the treemap (JSON)."""
    data = get_churn_data(repo_url)
    if not data:
        raise HTTPException(status_code=400, detail="Could not extract churn data.")
    return data

@app.get("/api/heatmap") #Legacy support for HTML response
async def get_heatmap_html(repo_url: str = Query(..., description="GitHub Repository URL")):
    """Returns an interactive Plotly Treemap as HTML (Legacy support)."""
    from fastapi.responses import HTMLResponse
    html_content = generate_plotly_heatmap(repo_url)
    if not html_content:
        raise HTTPException(status_code=400, detail="Could not generate heatmap.")
    return HTMLResponse(content=html_content)

@app.get("/api/file-history")
async def get_file_history_api(
    repo_url: str = Query(..., description="GitHub Repository URL"),
    file_path: str = Query(..., description="File path to get history for")
):
    """Returns commit history for a specific file."""
    data = get_file_history(repo_url, file_path)
    if not data:
        raise HTTPException(status_code=400, detail="Could not extract file history.")
    return data

@app.post("/api/review")
async def code_review_api(request: ReviewRequest):
    """Generates an AI-powered code review."""
    result = reviewer.generate_review(request.repo_url, request.github_token, request.commit_count)
    if "error" in result:
        # Check if it's a verification error (403) or general error (500)
        status_code = 403 if "ownership" in result["error"].lower() else 500
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)

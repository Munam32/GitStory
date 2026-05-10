import os
import json
import tempfile
import subprocess
import re
from pydriller import Repository
from git import Repo as GitRepo
import lizard
from openai import OpenAI
from github import Github, GithubException
from dotenv import load_dotenv

load_dotenv()

class CodeReviewer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )
        self.model = "nvidia/nemotron-3-nano-30b-a3b:free"

    def verify_ownership(self, repo_url: str, token: str):
        """Verifies if the token owner has write or admin access to the repository."""
        try:
            g = Github(token)
            match = re.search(r"github\.com/([^/]+)/([^/.]+)", repo_url)
            if not match:
                return False, "Invalid GitHub URL format."
            
            full_repo_name = f"{match.group(1)}/{match.group(2)}"
            repo = g.get_repo(full_repo_name)
            
            user = g.get_user()
            permissions = repo.get_collaborator_permission(user.login)
            
            if permissions not in ["admin", "write"]:
                if repo.owner.login != user.login:
                    return False, "You do not have ownership or write access to this repository."
            return True, None
        except GithubException as e:
            return False, f"GitHub verification failed: {e.data.get('message', str(e))}"
        except Exception as e:
            return False, f"Ownership verification error: {str(e)}"

    def analyze_with_lizard(self, source_code: str, filename: str) -> dict:
        try:
            analysis = lizard.analyze_file.analyze_source_code(filename, source_code)
            return {
                "complexity": analysis.average_cyclomatic_complexity,
                "nloc": analysis.nloc
            }
        except Exception:
            return {"error": "Analysis failed"}

    def run_semgrep(self, target_dir: str) -> list:
        print("Running Semgrep...")
        cmd = f'semgrep scan --config auto --json "{target_dir}"'
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            data = json.loads(result.stdout)
            return [
                {
                    "rule": f["check_id"], 
                    "severity": f["extra"]["severity"],
                    "message": f["extra"]["message"], 
                    "file": f["path"].replace(target_dir, ""),
                    "line": f["start"]["line"]
                }
                for f in data.get("results", [])
            ]
        except Exception as e:
            print(f"⚠️ Semgrep Error: {e}")
            return []

    def calculate_health_score(self, semgrep_results: list, extracted_data: list) -> int:
        score = 100
        for finding in semgrep_results:
            sev = finding.get("severity", "").upper()
            if sev == "ERROR":
                score -= 10
            elif sev == "WARNING":
                score -= 5
            else:
                score -= 2
        for file in extracted_data:
            complexity = file.get("metrics", {}).get("complexity", 0)
            if complexity > 15:
                score -= 5
            elif complexity > 10:
                score -= 2
        return max(0, min(100, score))

    def generate_review(self, repo_url: str, github_token: str, commit_count: int = 1):
        if not self.api_key:
            return {"error": "OPENROUTER_API_KEY is not set."}

        is_owner, error = self.verify_ownership(repo_url, github_token)
        if not is_owner:
            return {"error": error}

        extracted_data = []
        semgrep_results = []
        
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            authenticated_url = repo_url
            if "github.com" in repo_url:
                authenticated_url = repo_url.replace("https://", f"https://{github_token}@")

            print(f"Cloning {repo_url} locally...")
            try:
                GitRepo.clone_from(authenticated_url, temp_dir)
            except Exception as e:
                error_msg = str(e)
                if "Clone succeeded, but checkout failed" not in error_msg:
                    return {"error": f"Initial Git clone failed: {error_msg}"}

            try:
                semgrep_results = self.run_semgrep(temp_dir)
            except Exception as e:
                print(f"⚠️ Semgrep failed: {e}")

            try:
                repo = Repository(temp_dir, only_no_merge=True) 
                commits = list(repo.traverse_commits())[-commit_count:]
                
                for commit in commits:
                    for mod_file in commit.modified_files:
                        if mod_file.diff and mod_file.source_code:
                            extracted_data.append({
                                "filename": mod_file.filename,
                                "diff": mod_file.diff,
                                "metrics": self.analyze_with_lizard(mod_file.source_code, mod_file.filename)
                            })
            except Exception as e:
                 return {"error": f"Git Diff analysis failed: {str(e)}"}

        if not extracted_data:
            return {"message": "No specific source code changes found. Try increasing commit_count."}

        heuristic_score = self.calculate_health_score(semgrep_results, extracted_data)
        
        prompt = f"""
        You are an expert Senior Software Engineer. Perform a technical code review based strictly on the provided data.
        Your first line MUST be: HEALTH_SCORE: <score> (where <score> is 0-100).
        Base this score on code quality, security, and complexity.
        Format your response in Markdown:
        ## 1. Executive Summary
        ## 2. Security Findings
        ## 3. Code Structure & Complexity
        ## 4. Line-by-Line Feedback
        EVERY detected issue MUST include:
        - **Severity Tag:** [Critical], [Warning], or [Info]
        - **Location:** File: <path>, Line: <number>
        - **Suggestion:** A meaningful, actionable suggestion for resolution.
        ### System Findings:
        **Semgrep Findings:**
        {json.dumps(semgrep_results[:15], indent=2)} 
        **Recent Commit Diffs & Metrics:**
        """
        for file in extracted_data:
            prompt += f"\n#### File: {file['filename']}\nMetrics: {file['metrics']}\nDiff:\n```diff\n{file['diff']}\n```\n"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            full_review = response.choices[0].message.content
            
            health_score = heuristic_score
            score_match = re.search(r"HEALTH_SCORE:\s*(\d+)", full_review)
            if score_match:
                health_score = int(score_match.group(1))

            return {
                "repo": repo_url,
                "files_analyzed": [f["filename"] for f in extracted_data],
                "health_score": health_score,
                "review": full_review
            }
        except Exception as e:
            return {"error": f"Review generation failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    app = FastAPI()
    reviewer = CodeReviewer()
    
    @app.post("/review")
    async def review(request: dict):
        return reviewer.generate_review(request["repo_url"], request["github_token"], request.get("commit_count", 1))
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

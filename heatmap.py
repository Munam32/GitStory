import os
import pandas as pd
import plotly.express as px
from pydriller import Repository
from utils import parse_repo_url
#Legacy function - do not use in new code

def get_churn_data(repo_url: str):
    """
    Returns raw churn data as a list of dictionaries.
    Used by the React frontend.
    """
    print(f"--- DEBUG: Starting get_churn_data for {repo_url} ---")
    file_stats = {}
    try:
        base_url, branch = parse_repo_url(repo_url)
        
        kwargs = {}
        if branch:
            kwargs['only_in_branch'] = branch

        def traverse():
            for commit in Repository(base_url, **kwargs).traverse_commits():
                for modified_file in commit.modified_files:
                    path = modified_file.new_path or modified_file.old_path
                    if not path:
                        continue
                    
                    # Filter out non-code files
                    ignored_ext = ('.md', '.txt', '.png', '.jpg', '.gitignore', '.yml', '.json', '.csv', '.lock')
                    if any(path.endswith(ext) for ext in ignored_ext):
                        continue

                    if path not in file_stats:
                        file_stats[path] = {
                            "name": os.path.basename(path),
                            "path": path,
                            "churn_score": 0,
                            "total_commits": 0,
                            "last_modified": commit.author_date.isoformat()
                        }
                    
                    file_stats[path]["churn_score"] += (modified_file.added_lines + modified_file.deleted_lines)
                    file_stats[path]["total_commits"] += 1
                    file_stats[path]["last_modified"] = commit.author_date.isoformat()

        try:
            traverse()
        except Exception as branch_err:
            if branch:
                print(f"--- DEBUG: Churn branch traversal failed for '{branch}', falling back: {branch_err}")
                kwargs.pop('only_in_branch', None)
                traverse()
            else:
                raise branch_err

        return list(file_stats.values())
    except Exception as e:
        print(f"Error extracting churn data: {e}")
        return []

def generate_plotly_heatmap(repo_url: str):
    """
    Generates an interactive Plotly Treemap as HTML.
    Preserves legacy functionality.
    """
    data = get_churn_data(repo_url)
    if not data:
        return None

    df = pd.DataFrame(data)
    df['Repository'] = 'Root'
    df['Directory'] = df['path'].apply(lambda x: os.path.dirname(x) if os.path.dirname(x) else 'Top-Level')
    df['FileName'] = df['name']
    df['ChurnScore'] = df['churn_score']

    fig = px.treemap(
        df,
        path=['Repository', 'Directory', 'FileName'],
        values='ChurnScore',
        color='ChurnScore',
        color_continuous_scale='RdYlBu_r',
        title=f'Code Churn Heatmap: {repo_url}',
        hover_data=['ChurnScore']
    )
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    return fig.to_html(full_html=True, include_plotlyjs='cdn')

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse
    app = FastAPI()
    
    @app.get("/api/heatmap", response_class=HTMLResponse)
    def get_heatmap(repo_url: str):
        html = generate_plotly_heatmap(repo_url)
        if not html:
            raise HTTPException(status_code=400, detail="Could not generate heatmap.")
        return HTMLResponse(content=html)
    
    uvicorn.run(app, host="0.0.0.0", port=9000)

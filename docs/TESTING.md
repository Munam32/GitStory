# Testing GitStory

GitStory consists of a Next.js frontend and a single FastAPI backend.

## 1. Prerequisites
- Python 3.10+
- Node.js 18+
- GitHub Personal Access Token (for private repos and code review)
- `OPENROUTER_API_KEY` in the root `.env`

## 2. Backend

```bash
cd backend
pip install -r requirements.txt
python run.py            # http://localhost:8005
```

### Automated tests
```bash
cd backend
pytest                   # tests/ (parser, module map, docgen models)
pytest tests/test_parser.py
```

`tests/live/` is excluded by default. Those scripts need a running backend, network access, or API keys. Run them directly, for example `python -m tests.live.test_api` from `backend/`.

## 3. Frontend

```bash
cd frontend
npm install
npm run dev              # http://localhost:3000
```

Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` to the backend URL.

## 4. Features to Test

- **Dashboard (`/dashboard`)**: analyze a repository.
- **Chat (`/dashboard/chat`)**: index a repository and chat with its codebase.
- **Timeline (`/dashboard/timeline`)**: narrated history of the project.
- **Hotzones (`/dashboard/hotzones`)**: file churn treemap.
- **Stats / Collaborators**: repository statistics and contributor insights.

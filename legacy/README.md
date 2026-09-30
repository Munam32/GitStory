# Legacy code

Kept for reference only. Nothing in here is imported by the app, and none of it runs as-is.

| File | What it was |
|---|---|
| `server.py` | Original standalone RAG API (port 8000). Superseded by `backend/src/routes/integrations.py`. |
| `api.py` | Original standalone analysis API (timeline, hotzone, review; port 8002). Superseded by the same router. |
| `documentation.py`, `documentation_service.py`, `documentation_worker.py` | Scaffolding for a Celery-based docs service. They use relative imports into a package layout (`services/documentation/...`, `workers/`) that never existed in this repo. The working docs pipeline is `backend/src/docgen/`. |

The modules these files imported now live under `backend/src/analysis/`, `backend/src/rag/` and `backend/src/docgen/`.

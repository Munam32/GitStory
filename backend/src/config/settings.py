import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BACKEND_DIR.parent

# Root .env is the documented location; backend/.env (if present) overrides it
load_dotenv(REPO_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env", override=True)


def _resolve(path: str) -> str:
    """Resolve a relative path against backend/ so it doesn't depend on the CWD."""
    p = Path(path)
    return str(p if p.is_absolute() else (BACKEND_DIR / p).resolve())


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/gitstory"

    # JWT
    jwt_secret: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""

    # GitHub API
    github_token: str = ""

    # AI/LLM
    openai_api_key: str = ""
    gemini_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # CORS
    frontend_url: str = "http://localhost:3000"

    # Runtime data (relative paths are resolved against backend/)
    rag_chroma_path: str = "data/chroma_db"
    rag_maps_dir: str = "data/project_maps"
    rag_repos_dir: str = "data/repos"
    analysis_repos_dir: str = "data/analysis_repos"

    @property
    def chroma_path(self) -> str:
        return _resolve(self.rag_chroma_path)

    @property
    def maps_dir(self) -> str:
        return _resolve(self.rag_maps_dir)

    @property
    def repos_dir(self) -> str:
        return _resolve(self.rag_repos_dir)

    @property
    def analysis_dir(self) -> str:
        return _resolve(self.analysis_repos_dir)

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
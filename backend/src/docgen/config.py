from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str = "your-supabase-url"
    supabase_service_key: str = "your-supabase-key"
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"

def get_settings():
    return Settings()
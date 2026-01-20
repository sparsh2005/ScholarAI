"""Configuration management for ScholarAI backend."""

from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Settings
    app_name: str = "ScholarAI"
    debug: bool = True
    api_prefix: str = "/api"
    
    # OpenAI Settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    
    # Vector Store Settings
    chroma_persist_directory: str = "./data/chroma"
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Document Processing Settings
    upload_directory: str = "./data/uploads"
    processed_directory: str = "./data/processed"
    max_file_size_mb: int = 50
    
    # Chunking Settings
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    # CORS Settings - Allow multiple local dev ports
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:4173",  # Vite preview
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create required directories
def init_directories():
    """Initialize required data directories."""
    settings = get_settings()
    
    directories = [
        settings.chroma_persist_directory,
        settings.upload_directory,
        settings.processed_directory,
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

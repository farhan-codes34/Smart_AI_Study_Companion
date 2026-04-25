"""
config.py — Central configuration loaded from .env

Why a single config module?
  All settings come from one place. If you change a path or model,
  you change it here (or in .env) — nothing else needs to be touched.
"""

import os
from dotenv import load_dotenv

# Load .env file from the backend/ directory
load_dotenv()


class Settings:
    # Groq LLM
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Storage paths
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    AUDIO_DIR: str = os.getenv("AUDIO_DIR", "./data/audio")

    # Models
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Chunking
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))

    # FastAPI metadata
    APP_TITLE: str = "Smart AI Study Companion"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "AI-powered study tool: upload notes → get explanations, "
        "quizzes, and voice Q&A powered by RAG + Groq LLM."
    )


# Single shared instance — import this everywhere
settings = Settings()

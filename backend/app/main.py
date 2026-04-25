"""
main.py — FastAPI application entry point

This file:
  1. Creates the FastAPI app with metadata from config
  2. Mounts all route files (one per feature)
  3. Adds CORS so the Streamlit frontend can talk to it
  4. Ensures required data directories exist on startup
"""

import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes.health import router as health_router

# ── Route imports (uncommented phase by phase) ───────────────────────────────
from app.routes.upload import router as upload_router
from app.routes.explain import router as explain_router
from app.routes.ask import router as ask_router
from app.routes.quiz import router as quiz_router
from app.routes.voice import router as voice_router
from app.routes.flashcards import router as flashcards_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        # OpenAPI docs available at /docs (Swagger) and /redoc
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Allows Streamlit (running on localhost:8501) to call this API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Static files (serve generated audio back to Streamlit) ───────────────
    os.makedirs(settings.AUDIO_DIR, exist_ok=True)
    app.mount("/audio", StaticFiles(directory=settings.AUDIO_DIR), name="audio")

    # ── Routes ───────────────────────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(upload_router, prefix="/api")
    app.include_router(explain_router, prefix="/api")
    app.include_router(ask_router, prefix="/api")
    app.include_router(quiz_router, prefix="/api")
    app.include_router(voice_router, prefix="/api")
    app.include_router(flashcards_router, prefix="/api")

    return app


# ── Startup: make sure all data folders exist ────────────────────────────────
app = create_app()

@app.on_event("startup")
async def startup_event():
    # Ensure all data directories exist
    for folder in [settings.UPLOAD_DIR, settings.CHROMA_DB_PATH, settings.AUDIO_DIR]:
        os.makedirs(folder, exist_ok=True)

    # Pre-load the embedding model at startup.
    # WHY asyncio.to_thread?
    #   SentenceTransformer.encode() is a blocking (synchronous) call.
    #   Running it directly inside an async function would freeze the
    #   entire event loop. asyncio.to_thread() runs it in a background
    #   thread so FastAPI stays responsive while the model loads.
    # Pre-load embedding model
    print("⏳ Pre-loading embedding model...")
    from app.services.embedder import embed_texts
    await asyncio.to_thread(embed_texts, ["warmup"])
    print("✅ Embedding model ready.")

    # Pre-load Whisper model (STT) — ~140 MB download on first run
    print("⏳ Pre-loading Whisper STT model...")
    from app.services.stt_service import _get_model
    await asyncio.to_thread(_get_model)
    print("✅ Whisper model ready.")

    print(f"✅ {settings.APP_TITLE} v{settings.APP_VERSION} started.")
    print(f"   Docs: http://127.0.0.1:8000/docs")

"""
main.py — FastAPI application entry point

This file:
  1. Creates the FastAPI app with metadata from config
  2. Mounts all route files (one per feature)
  3. Adds CORS so the Streamlit frontend can talk to it
  4. Ensures required data directories exist on startup
"""

import os
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
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
    for folder in [settings.UPLOAD_DIR, settings.CHROMA_DB_PATH, settings.AUDIO_DIR]:
        os.makedirs(folder, exist_ok=True)
    print(f"✅ {settings.APP_TITLE} v{settings.APP_VERSION} started.")

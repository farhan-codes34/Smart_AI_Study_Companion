"""
embedder.py — Convert text into dense vector embeddings

WHY embeddings (core GenAI concept):
  A string like "photosynthesis" and "how plants make food" look
  completely different as text. As vectors they land very close together
  in 384-dimensional space because they MEAN the same thing.
  This semantic similarity is what powers the RAG retrieval step:
  a user's question is embedded and the closest document chunks are
  returned — even if they use different words.

Model: all-MiniLM-L6-v2
  - 384-dimensional output vectors
  - ~22M parameters — small enough to run on CPU in seconds
  - Trained specifically for semantic similarity tasks
  - No API key needed — runs 100% locally
"""

from __future__ import annotations  # makes X | None a string at runtime, not evaluated

from sentence_transformers import SentenceTransformer
from app.config import settings

# ── Singleton model instance ──────────────────────────────────────────────────
# WHY singleton?
#   Loading the model takes ~1-2 seconds and downloads ~90 MB on first run.
#   By loading it once at module import time and reusing the same instance,
#   every subsequent call to embed_text() is instant.
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Load the model once and cache it for the lifetime of the process."""
    global _model
    if _model is None:
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL} ...")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        print("Embedding model loaded.")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of text strings into a list of embedding vectors.

    WHY batch processing?
      SentenceTransformer can process many texts in one GPU/CPU pass.
      Batching is much faster than calling the model once per chunk.

    Args:
        texts: List of text strings (chunks, questions, etc.)

    Returns:
        List of vectors. Each vector is a list of 384 floats.
        Order matches the input list exactly.
    """
    if not texts:
        return []

    model = _get_model()

    # show_progress_bar=False keeps server logs clean
    # convert_to_python avoids numpy dependency downstream
    embeddings = model.encode(
        texts,
        show_progress_bar=False,
        convert_to_numpy=True,
    )

    # Convert numpy array → plain Python lists for JSON serialisation
    return [emb.tolist() for emb in embeddings]


def embed_query(query: str) -> list[float]:
    """
    Embed a single query string (e.g. a user's question).

    This is a convenience wrapper around embed_texts() for the common
    case of embedding one string at a time during RAG retrieval.

    Args:
        query: The user's question or search text.

    Returns:
        A single embedding vector (list of 384 floats).
    """
    results = embed_texts([query])
    return results[0] if results else []

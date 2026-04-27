"""
embedder.py — Convert text into dense vector embeddings using FastEmbed

WHY FastEmbed instead of sentence-transformers?
  sentence-transformers loads the full PyTorch stack (~400 MB RAM).
  FastEmbed uses ONNX Runtime with a quantized model (~80 MB RAM).
  Same all-MiniLM-L6-v2 model, same 384-dim output — but 5x lighter.
  Critical for Render free tier which has only 512 MB RAM total.

Model: all-MiniLM-L6-v2 (via fastembed)
  - 384-dimensional output vectors
  - ONNX int8 quantized — fast CPU inference
  - No PyTorch required
"""

from __future__ import annotations

from fastembed import TextEmbedding

# ── Singleton model instance ──────────────────────────────────────────────────
_model: TextEmbedding | None = None


def _get_model() -> TextEmbedding:
    """Load the ONNX model once and cache it for the lifetime of the process."""
    global _model
    if _model is None:
        print("Loading embedding model (fastembed all-MiniLM-L6-v2)...")
        _model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        print("Embedding model loaded.")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of text strings into embedding vectors.

    Args:
        texts: List of text strings (chunks, questions, etc.)

    Returns:
        List of vectors. Each vector is a list of 384 floats.
    """
    if not texts:
        return []

    model = _get_model()
    embeddings = list(model.embed(texts))
    return [emb.tolist() for emb in embeddings]


def embed_query(query: str) -> list[float]:
    """
    Embed a single query string (e.g. a user's question).

    Args:
        query: The user's question or search text.

    Returns:
        A single embedding vector (list of 384 floats).
    """
    results = embed_texts([query])
    return results[0] if results else []

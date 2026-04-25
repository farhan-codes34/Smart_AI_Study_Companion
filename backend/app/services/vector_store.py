"""
vector_store.py — ChromaDB wrapper for storing and searching embeddings

WHY a vector database (core GenAI concept):
  A regular database searches by exact match or keyword.
  A vector database searches by MEANING — it finds the chunks whose
  embedding vectors are closest to the query vector in high-dimensional
  space. This is what makes RAG work: "What is ATP?" retrieves the
  chunk about "adenosine triphosphate energy currency" even though
  the words don't overlap.

ChromaDB specifics:
  - Runs entirely locally (no cloud account needed)
  - Persists data to disk at CHROMA_DB_PATH
  - Each uploaded document gets its own "collection" (like a table)
  - Similarity metric: cosine distance (standard for text embeddings)
"""

from __future__ import annotations  # makes X | None a string at runtime, not evaluated

import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings


# ── Singleton client ──────────────────────────────────────────────────────────
# WHY singleton? Same reason as embedder.py — opening the DB connection
# once and reusing it is much faster than reconnecting on every request.
_client: chromadb.PersistentClient | None = None


def _get_client() -> chromadb.PersistentClient:
    """Return the shared ChromaDB client, creating it if needed."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


# ── Collection helpers ────────────────────────────────────────────────────────

def get_or_create_collection(collection_name: str) -> chromadb.Collection:
    """
    Return an existing collection or create a new one.

    WHY one collection per document?
      Keeping documents separate lets users query a specific document
      rather than mixing results from all uploaded files.
      Collection name = sanitised filename (e.g. "lecture_3_pdf").

    Args:
        collection_name: Unique name for this document's collection.
    """
    client = _get_client()
    return client.get_or_create_collection(
        name=collection_name,
        # cosine distance: measures angle between vectors (best for text)
        metadata={"hnsw:space": "cosine"},
    )


def collection_exists(collection_name: str) -> bool:
    """Check whether a collection (document) has already been indexed."""
    client = _get_client()
    existing = [c.name for c in client.list_collections()]
    return collection_name in existing


def list_collections() -> list[str]:
    """Return names of all indexed document collections."""
    client = _get_client()
    return [c.name for c in client.list_collections()]


def delete_collection(collection_name: str) -> None:
    """Delete a document's collection and all its embeddings."""
    client = _get_client()
    client.delete_collection(collection_name)


# ── Core operations ───────────────────────────────────────────────────────────

def add_chunks(
    collection_name: str,
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
) -> None:
    """
    Store text chunks + their embedding vectors in ChromaDB.

    ChromaDB requires:
      - ids:        unique string ID per chunk
      - documents:  the raw text (stored for retrieval)
      - embeddings: the vector representation
      - metadatas:  any extra info (filename, chunk_index, etc.)

    Args:
        collection_name: Which collection to add to.
        chunks:          Raw text for each chunk.
        embeddings:      Corresponding embedding vectors.
        metadatas:       Metadata dicts (one per chunk).
    """
    collection = get_or_create_collection(collection_name)

    # Generate unique IDs: "chunk_0", "chunk_1", ...
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def similarity_search(
    collection_name: str,
    query_embedding: list[float],
    top_k: int = 3,
) -> list[dict]:
    """
    Find the top-k most semantically similar chunks to a query vector.

    WHY this is the heart of RAG:
      The query (user's question) is embedded into a vector.
      We then ask ChromaDB: "which stored vectors are closest?"
      Those closest chunks = the most relevant parts of the document.
      We pass those to the LLM as context → grounded, accurate answers.

    Args:
        collection_name: Which document collection to search.
        query_embedding: The embedded user question (384-dim vector).
        top_k:           How many chunks to retrieve (default 3).

    Returns:
        List of dicts with keys: 'text', 'metadata', 'distance'
        Sorted by relevance (most relevant first).
    """
    collection = get_or_create_collection(collection_name)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),  # can't ask for more than exists
        include=["documents", "metadatas", "distances"],
    )

    # Unpack ChromaDB's nested list format into a clean list of dicts
    retrieved: list[dict] = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        retrieved.append({
            "text":     doc,
            "metadata": meta,
            "distance": dist,   # lower = more similar (cosine distance)
        })

    return retrieved


def get_all_chunks(collection_name: str) -> list[str]:
    """
    Retrieve every chunk from a collection (used by Explain feature
    when no specific query is given — explain the whole document).

    Returns:
        List of raw text chunks in insertion order.
    """
    collection = get_or_create_collection(collection_name)
    count = collection.count()

    if count == 0:
        return []

    results = collection.get(include=["documents"])
    return results["documents"]

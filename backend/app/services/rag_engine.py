"""
rag_engine.py — Retrieval-Augmented Generation core (core GenAI concept: RAG)

WHY RAG?
  A plain LLM answers from its training data — it may hallucinate, give
  outdated info, or simply not know YOUR lecture notes.

  RAG fixes this by:
    1. RETRIEVE:  embed the user's question → find the most relevant
                  chunks from THEIR document in ChromaDB
    2. AUGMENT:   inject those chunks into the LLM prompt as context
    3. GENERATE:  instruct the LLM to answer ONLY from that context

  Result: answers that are accurate, grounded, and cite the student's
  own material — not generic internet knowledge.

This module is shared by:
  - Explain feature  (retrieves relevant chunks for a topic)
  - Voice Q&A        (retrieves context for a spoken question)
"""

from app.services.embedder import embed_query
from app.services.vector_store import similarity_search, get_all_chunks


def retrieve_context(
    collection_name: str,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Embed the query and retrieve the top-k most relevant chunks.

    Args:
        collection_name: Which ChromaDB collection (document) to search.
        query:           The user's question or topic string.
        top_k:           Number of chunks to retrieve.

    Returns:
        List of result dicts: {'text', 'metadata', 'distance'}
        Sorted by relevance (most relevant first — lowest cosine distance).
    """
    query_vector = embed_query(query)
    return similarity_search(collection_name, query_vector, top_k=top_k)


def build_context_string(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a single readable context block.

    WHY label chunks?
      Labels like [Chunk 1] help the LLM understand where one piece
      of content ends and another begins. This improves coherence when
      the LLM synthesises information across multiple chunks.

    Args:
        chunks: List returned by retrieve_context() or similarity_search().

    Returns:
        Formatted multi-chunk context string ready to inject into a prompt.
    """
    if not chunks:
        return "No relevant content found."

    parts = []
    for i, chunk in enumerate(chunks, start=1):
        text = chunk.get("text", "").strip()
        if text:
            parts.append(f"[Chunk {i}]\n{text}")

    return "\n\n---\n\n".join(parts)


def get_document_context(collection_name: str, max_chunks: int = 10) -> str:
    """
    Get a broad overview context from a document (used when no specific
    query is given — e.g. "explain this whole document").

    Returns the first `max_chunks` chunks joined as a context string.
    We take the first chunks because they usually contain introductory
    material that gives the best high-level overview.

    Args:
        collection_name: ChromaDB collection to read from.
        max_chunks:      How many chunks to include in context.

    Returns:
        Formatted context string.
    """
    all_chunks = get_all_chunks(collection_name)
    selected = all_chunks[:max_chunks]

    # Wrap in same format as retrieve_context output for consistency
    wrapped = [{"text": c, "metadata": {}, "distance": 0.0} for c in selected]
    return build_context_string(wrapped)

"""
chunker.py — Split raw text into overlapping chunks for embedding

WHY chunking matters (core GenAI concept):
  LLMs have a context window limit. A 50-page PDF cannot fit in one prompt.
  Chunking breaks the document into small pieces that:
    1. Fit inside the LLM context window
    2. Can be individually embedded into vectors
    3. Allow RAG to retrieve only the RELEVANT pieces (not the whole doc)

WHY overlap?
  If a sentence is split across a chunk boundary, meaning is lost.
  Overlapping 50 tokens between chunks ensures no idea is cut in half.

Strategy — RecursiveCharacterTextSplitter:
  Tries to split on paragraph breaks (\n\n) first, then sentence
  breaks (\n), then spaces, and finally characters as a last resort.
  This preserves natural language boundaries wherever possible.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings


def chunk_text(text: str) -> list[str]:
    """
    Split a document string into overlapping chunks.

    Args:
        text: Raw extracted text from document_loader.

    Returns:
        List of text chunks. Each chunk is ≤ CHUNK_SIZE characters
        with CHUNK_OVERLAP characters shared with its neighbours.

    WHY characters not tokens?
      Exact token counts require running a tokeniser (slow).
      Character count is a fast, good-enough approximation:
      ~4 chars ≈ 1 token for English text, so 500 tokens ≈ 2000 chars.
      We keep CHUNK_SIZE in the .env as tokens for conceptual clarity
      but multiply by 4 here for the splitter.
    """
    if not text or not text.strip():
        return []

    # Convert token counts → approximate character counts
    chunk_size_chars    = settings.CHUNK_SIZE * 4     # 500 tokens × 4 = 2000 chars
    chunk_overlap_chars = settings.CHUNK_OVERLAP * 4  # 50 tokens  × 4 = 200 chars

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size_chars,
        chunk_overlap=chunk_overlap_chars,
        # Split hierarchy: paragraph → sentence → word → character
        separators=["\n\n", "\n", " ", ""],
        # Keep track of character positions (useful for future citation features)
        add_start_index=False,
    )

    chunks: list[str] = splitter.split_text(text)

    # Filter out chunks that are just whitespace or very short (< 30 chars)
    # These usually come from headers or page markers and add noise to RAG
    chunks = [c.strip() for c in chunks if len(c.strip()) >= 30]

    return chunks


def get_chunk_metadata(
    chunks: list[str],
    filename: str,
    collection_name: str,
) -> list[dict]:
    """
    Build a metadata dict for each chunk.

    WHY store metadata?
      ChromaDB stores metadata alongside each vector.
      When we retrieve chunks during RAG, we can show the user
      WHICH document and chunk the answer came from — transparency.

    Args:
        chunks:          List of text chunks.
        filename:        Original uploaded filename (e.g. "lecture_3.pdf").
        collection_name: ChromaDB collection name for this document.

    Returns:
        List of metadata dicts, one per chunk.
    """
    return [
        {
            "filename":        filename,
            "collection_name": collection_name,
            "chunk_index":     i,
            "total_chunks":    len(chunks),
            "char_count":      len(chunk),
        }
        for i, chunk in enumerate(chunks)
    ]

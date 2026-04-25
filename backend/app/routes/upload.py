"""
upload.py — POST /api/upload endpoint

Flow:
  1. Receive file from Streamlit frontend (multipart form)
  2. Save it to disk (UPLOAD_DIR)
  3. Extract text → chunk → embed → store in ChromaDB
  4. Return how many chunks were stored

WHY save to disk first?
  pdfplumber and pytesseract need a file path, not an in-memory buffer.
  Saving also lets us re-process the file later without re-uploading.
"""

import os
import re
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import settings
from app.models.schemas import UploadResponse
from app.services.document_loader import load_document, ALL_ALLOWED
from app.services.chunker import chunk_text, get_chunk_metadata
from app.services.embedder import embed_texts
from app.services.vector_store import add_chunks, delete_collection, collection_exists, list_collections

router = APIRouter()


def _sanitise_collection_name(filename: str) -> str:
    """
    Convert a filename into a valid ChromaDB collection name.

    ChromaDB rules: 3-63 chars, alphanumeric + underscores/hyphens,
    must start and end with alphanumeric character.

    Example: "Lecture 3 (Final).pdf" → "lecture_3_final_pdf"
    """
    # Replace dots, spaces, brackets with underscores
    name = re.sub(r"[^\w]", "_", filename.lower())
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name)
    # Strip leading/trailing underscores
    name = name.strip("_")
    # Truncate to 63 chars
    name = name[:63]
    # Ensure it starts with a letter (prepend 'doc' if not)
    if name and not name[0].isalpha():
        name = "doc_" + name
    return name or "document"


@router.post("/upload", response_model=UploadResponse, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload a PDF, TXT, or image file and index it in ChromaDB.

    The file is:
      1. Validated (extension check)
      2. Saved to disk
      3. Text-extracted (PDF / TXT / OCR)
      4. Chunked (500-token chunks, 50-token overlap)
      5. Embedded (all-MiniLM-L6-v2)
      6. Stored in ChromaDB under a collection named after the file
    """
    # ── 1. Validate file extension + size ────────────────────────────────────
    filename = file.filename or "upload"
    ext = os.path.splitext(filename)[1].lower()

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

    if ext not in ALL_ALLOWED:
        raise HTTPException(
            status_code=400,
            detail=(
                f"File type '{ext}' is not supported. "
                f"Allowed types: {', '.join(sorted(ALL_ALLOWED))}"
            ),
        )

    # ── 2. Save file to disk ──────────────────────────────────────────────────
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(settings.UPLOAD_DIR, filename)

    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({len(content) / 1024 / 1024:.1f} MB). Maximum allowed size is 50 MB.",
            )
        with open(save_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # ── 3. Extract text ───────────────────────────────────────────────────────
    try:
        raw_text = load_document(save_path)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from the file."
        )

    # ── 4. Chunk text ─────────────────────────────────────────────────────────
    chunks = chunk_text(raw_text)

    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="Document was too short to produce any chunks after processing."
        )

    # ── 5. Generate collection name ───────────────────────────────────────────
    collection_name = _sanitise_collection_name(filename)

    # If the same file was uploaded before, delete the old index and re-index
    if collection_exists(collection_name):
        delete_collection(collection_name)

    # ── 6. Embed chunks ───────────────────────────────────────────────────────
    try:
        embeddings = embed_texts(chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")

    # ── 7. Store in ChromaDB ──────────────────────────────────────────────────
    metadatas = get_chunk_metadata(chunks, filename, collection_name)

    try:
        add_chunks(collection_name, chunks, embeddings, metadatas)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector store error: {e}")

    return UploadResponse(
        filename=filename,
        collection_name=collection_name,
        chunks_stored=len(chunks),
        message=(
            f"Successfully indexed '{filename}' into {len(chunks)} chunks. "
            f"Collection: '{collection_name}'"
        ),
    )


@router.get("/documents", tags=["Documents"])
async def list_documents() -> dict:
    """Return all document collection names currently stored in ChromaDB."""
    return {"collections": list_collections()}

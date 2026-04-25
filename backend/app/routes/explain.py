"""
explain.py — POST /api/explain endpoint

Flow:
  1. Receive collection_name + optional topic from Streamlit
  2. Retrieve relevant chunks from ChromaDB (RAG)
  3. Build explanation prompt with retrieved context
  4. Call Groq LLM
  5. Parse JSON response into ExplainResponse schema
  6. Return to frontend
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import ExplainRequest, ExplainResponse
from app.services.rag_engine import retrieve_context, build_context_string, get_document_context
from app.services.vector_store import collection_exists
from app.services.llm_service import generate
from app.services.json_parser import extract_json
from app.prompts.explain_prompt import EXPLAIN_SYSTEM_PROMPT, build_explain_prompt

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse, tags=["Explain"])
async def explain_document(request: ExplainRequest) -> ExplainResponse:
    """
    Generate a simplified explanation of a document or specific topic.

    Uses RAG to retrieve the most relevant chunks, then asks the LLM
    to explain them in plain language with key points and an analogy.
    All output is strictly grounded in the uploaded document content.
    """
    # ── 1. Verify the collection exists ──────────────────────────────────────
    if not collection_exists(request.collection_name):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Collection '{request.collection_name}' not found. "
                "Please upload and index a document first."
            ),
        )

    # ── 2. Retrieve relevant context (RAG step) ───────────────────────────────
    try:
        if request.topic and request.topic.strip():
            # Topic given → semantic search for relevant chunks
            chunks = retrieve_context(
                collection_name=request.collection_name,
                query=request.topic,
                top_k=6,
            )
            context_str = build_context_string(chunks)
            source_texts = [c["text"] for c in chunks]
        else:
            # No topic → use first 8 chunks for a broad document overview
            context_str = get_document_context(
                collection_name=request.collection_name,
                max_chunks=8,
            )
            source_texts = [context_str]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {e}")

    # ── 3. Build prompt + call LLM ────────────────────────────────────────────
    user_prompt = build_explain_prompt(context=context_str, topic=request.topic)

    try:
        raw_response = generate(
            user_prompt=user_prompt,
            system_prompt=EXPLAIN_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=2048,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # ── 4. Parse JSON response ────────────────────────────────────────────────
    try:
        parsed = extract_json(raw_response)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # ── 5. Validate and return ────────────────────────────────────────────────
    explanation = parsed.get("explanation", "").strip()
    key_points  = parsed.get("key_points", [])
    analogy     = parsed.get("analogy", "").strip()

    if not explanation:
        raise HTTPException(
            status_code=500,
            detail="LLM returned empty explanation. Please try again."
        )

    # Ensure key_points is a list of strings
    if not isinstance(key_points, list):
        key_points = [str(key_points)]
    key_points = [str(kp).strip() for kp in key_points if str(kp).strip()]

    return ExplainResponse(
        explanation=explanation,
        key_points=key_points,
        analogy=analogy,
        source_chunks=source_texts[:5],  # return up to 5 chunks for transparency
    )

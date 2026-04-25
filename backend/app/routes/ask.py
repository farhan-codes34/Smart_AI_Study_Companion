"""
ask.py — POST /api/ask endpoint (text Q&A, RAG-powered)

Flow:
  1. Receive collection_name + question
  2. Embed question → retrieve top-4 relevant chunks (RAG)
  3. Build grounded prompt with retrieved context
  4. Call Groq LLM with strict no-hallucination instruction
  5. Parse JSON response
  6. Return answer + source chunks (transparency)

This endpoint is also called internally by the voice route (Phase 6),
which transcribes audio first and then calls this same logic.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import AskRequest, AskResponse
from app.services.rag_engine import retrieve_context, build_context_string
from app.services.vector_store import collection_exists
from app.services.llm_service import generate
from app.services.json_parser import extract_json
from app.prompts.qa_prompt import QA_SYSTEM_PROMPT, build_qa_prompt

router = APIRouter()


@router.post("/ask", response_model=AskResponse, tags=["Q&A"])
async def ask_question(request: AskRequest) -> AskResponse:
    """
    Answer a student's question using RAG over their uploaded document.

    The answer is strictly grounded in the document — the LLM is forbidden
    from using training data. If the answer isn't in the notes, it says so.
    """
    # ── 1. Verify collection exists ───────────────────────────────────────────
    if not collection_exists(request.collection_name):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Document '{request.collection_name}' not found. "
                "Upload and index a document first."
            ),
        )

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # ── 2. RAG — retrieve relevant chunks ─────────────────────────────────────
    try:
        chunks = retrieve_context(
            collection_name=request.collection_name,
            query=request.question,
            top_k=4,   # 4 chunks balances context richness vs prompt size
        )
        context_str = build_context_string(chunks)
        source_texts = [c["text"] for c in chunks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {e}")

    # ── 3. Build prompt + call LLM ────────────────────────────────────────────
    user_prompt = build_qa_prompt(context=context_str, question=request.question)

    try:
        raw_response = generate(
            user_prompt=user_prompt,
            system_prompt=QA_SYSTEM_PROMPT,
            temperature=0.2,    # low temp = more factual, less creative
            max_tokens=1024,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # ── 4. Parse JSON response ─────────────────────────────────────────────────
    try:
        parsed = extract_json(raw_response)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    answer = parsed.get("answer", "").strip()
    if not answer:
        raise HTTPException(status_code=500, detail="LLM returned an empty answer.")

    return AskResponse(
        question=request.question,
        answer=answer,
        source_chunks=source_texts,
    )

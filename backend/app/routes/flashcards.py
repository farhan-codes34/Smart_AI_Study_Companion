"""
flashcards.py — Flashcard generation endpoint

Endpoint:
  POST /api/flashcards — generates term-definition flashcards from a document

WHY flashcards as a separate phase?
  Flashcards target a different study mode than quizzes:
    - Quiz  → tests recall under pressure (exam simulation)
    - Cards → builds vocabulary and concept familiarity (spaced repetition)

  Both use the same RAG + LLM pipeline, demonstrating how a single
  backend architecture can power multiple learning modalities.

GenAI concepts demonstrated:
  - Structured output (LLM returns strict JSON term-definition pairs)
  - Grounded generation (only uses provided document context)
  - Broad document retrieval (needs coverage across the whole document)
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import FlashcardRequest, FlashcardResponse, Flashcard
from app.services.rag_engine import get_document_context
from app.services.vector_store import collection_exists
from app.services.llm_service import generate
from app.services.json_parser import extract_json
from app.prompts.flashcard_prompt import FLASHCARD_SYSTEM_PROMPT, build_flashcard_prompt

router = APIRouter()


def _parse_flashcard_response(raw: str) -> list[Flashcard]:
    """
    Parse and validate the LLM's JSON flashcard response.

    Skips any card with a blank term or definition rather than crashing.

    Args:
        raw: Raw LLM response string.

    Returns:
        List of validated Flashcard objects.

    Raises:
        ValueError: If JSON is unparseable or no valid cards found.
    """
    parsed = extract_json(raw)
    raw_cards = parsed.get("flashcards", [])

    if not raw_cards:
        raise ValueError("LLM returned no flashcards. Try again or use a longer document.")

    cards: list[Flashcard] = []
    seen_terms: set[str] = set()

    for card in raw_cards:
        term       = str(card.get("term", "")).strip()
        definition = str(card.get("definition", "")).strip()

        if not term or not definition:
            continue  # skip incomplete cards

        # Deduplicate by term (case-insensitive)
        term_lower = term.lower()
        if term_lower in seen_terms:
            continue
        seen_terms.add(term_lower)

        cards.append(Flashcard(term=term, definition=definition))

    if not cards:
        raise ValueError(
            "No valid flashcards could be parsed from the LLM response. Try generating again."
        )

    return cards


@router.post("/flashcards", response_model=FlashcardResponse, tags=["Flashcards"])
async def generate_flashcards(request: FlashcardRequest) -> FlashcardResponse:
    """
    Generate study flashcards (term + definition) from an indexed document.

    Uses broad document context so cards cover the whole document, not just
    one section. The LLM is instructed to avoid duplicates and pick specific
    named concepts — not vague or generic terms.
    """
    # ── 1. Verify collection ──────────────────────────────────────────────────
    if not collection_exists(request.collection_name):
        raise HTTPException(
            status_code=404,
            detail=f"Document '{request.collection_name}' not found. Upload it first.",
        )

    # ── 2. Get broad document context ─────────────────────────────────────────
    # Flashcards need wide coverage — take up to 20 chunks so the LLM can
    # pick diverse terms from across the whole document.
    try:
        context = get_document_context(
            collection_name=request.collection_name,
            max_chunks=min(20, request.num_cards * 2),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {e}")

    # ── 3. Build prompt + call LLM ────────────────────────────────────────────
    user_prompt = build_flashcard_prompt(context=context, num_cards=request.num_cards)

    try:
        raw_response = generate(
            user_prompt=user_prompt,
            system_prompt=FLASHCARD_SYSTEM_PROMPT,
            temperature=0.3,    # low temperature — factual term extraction
            max_tokens=4096,    # enough for 30 cards with full definitions
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # ── 4. Parse + validate flashcards ───────────────────────────────────────
    try:
        cards = _parse_flashcard_response(raw_response)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return FlashcardResponse(flashcards=cards, total=len(cards))

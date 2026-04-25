"""
schemas.py — Pydantic models for all API request/response bodies

Why Pydantic?
  FastAPI uses Pydantic to auto-validate incoming JSON, generate
  OpenAPI docs, and serialize responses. Defining schemas here
  keeps routes clean and gives us free type checking.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── Health ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    message: str


# ── Upload ──────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    filename: str
    collection_name: str       # ChromaDB collection the chunks landed in
    chunks_stored: int          # How many chunks were embedded and saved
    message: str


# ── Explain ─────────────────────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    collection_name: str = Field(..., description="ChromaDB collection to query")
    topic: Optional[str] = Field(
        None,
        description="Optional topic hint. If empty, explains the whole document."
    )

class ExplainResponse(BaseModel):
    explanation: str            # Plain-language explanation from the LLM
    key_points: list[str]       # Bullet list extracted from LLM output
    analogy: str                # Real-life analogy
    source_chunks: list[str]    # The RAG chunks used (for transparency)


# ── Quiz ────────────────────────────────────────────────────────────────────

class QuizQuestion(BaseModel):
    question: str
    options: list[str]          # Always 4 items: ["A. ...", "B. ...", ...]
    correct_answer: str         # e.g. "A"
    explanation: str            # Why that answer is correct

class QuizRequest(BaseModel):
    collection_name: str
    num_questions: int = Field(5, ge=1, le=20)

class QuizResponse(BaseModel):
    questions: list[QuizQuestion]

class EvaluateRequest(BaseModel):
    questions: list[QuizQuestion]
    answers: list[str]          # Student's chosen answer per question

class EvaluateResponse(BaseModel):
    score: int
    total: int
    percentage: float
    results: list[dict]         # Per-question: correct?, explanation


# ── Flashcards ──────────────────────────────────────────────────────────────

class Flashcard(BaseModel):
    term: str                   # Front of card — key concept or vocabulary
    definition: str             # Back of card — concise explanation

class FlashcardRequest(BaseModel):
    collection_name: str
    num_cards: int = Field(10, ge=5, le=30)

class FlashcardResponse(BaseModel):
    flashcards: list[Flashcard]
    total: int


# ── Voice / RAG Q&A ─────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    collection_name: str
    question: str               # Already transcribed text (text-only ask)

class AskResponse(BaseModel):
    question: str
    answer: str
    source_chunks: list[str]    # Retrieved context shown for transparency

class VoiceQueryResponse(BaseModel):
    transcribed_question: str
    answer: str
    audio_filename: str         # Served from /data/audio/

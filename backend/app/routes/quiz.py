"""
quiz.py — Quiz generation and evaluation endpoints

Endpoints:
  POST /api/generate-quiz  — generates MCQs from a document
  POST /api/evaluate-quiz  — scores student answers, returns results

WHY two endpoints?
  Separating generation from evaluation means the frontend can store
  the generated questions in session state and evaluate them later
  without regenerating (saves API calls and keeps results consistent).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    QuizRequest, QuizResponse, QuizQuestion,
    EvaluateRequest, EvaluateResponse,
)
from app.services.rag_engine import get_document_context
from app.services.vector_store import collection_exists
from app.services.llm_service import generate
from app.services.json_parser import extract_json
from app.prompts.quiz_prompt import QUIZ_SYSTEM_PROMPT, build_quiz_prompt

router = APIRouter()


def _parse_quiz_response(raw: str, expected_count: int) -> list[QuizQuestion]:
    """
    Parse and validate the LLM's JSON quiz response.

    WHY extra validation?
      The LLM may return fewer questions than asked, malformed options,
      or incorrect answer letters. We validate each field and skip
      broken questions rather than crashing the whole request.

    Args:
        raw:            Raw LLM response string.
        expected_count: How many questions were requested.

    Returns:
        List of validated QuizQuestion objects.

    Raises:
        ValueError: If JSON is unparseable or no valid questions found.
    """
    parsed = extract_json(raw)
    raw_questions = parsed.get("questions", [])

    if not raw_questions:
        raise ValueError("LLM returned no questions. Try again or use a longer document.")

    questions: list[QuizQuestion] = []
    valid_answers = {"A", "B", "C", "D"}

    for i, q in enumerate(raw_questions):
        # Validate required fields
        question_text = str(q.get("question", "")).strip()
        options       = q.get("options", [])
        correct       = str(q.get("correct_answer", "")).strip().upper()
        explanation   = str(q.get("explanation", "")).strip()

        if not question_text:
            continue  # skip blank questions
        if len(options) != 4:
            continue  # skip malformed option lists
        if correct not in valid_answers:
            continue  # skip invalid answer letters

        questions.append(QuizQuestion(
            question=question_text,
            options=[str(o).strip() for o in options],
            correct_answer=correct,
            explanation=explanation or "No explanation provided.",
        ))

    if not questions:
        raise ValueError(
            "No valid questions could be parsed from the LLM response. "
            "Try generating again."
        )

    return questions


@router.post("/generate-quiz", response_model=QuizResponse, tags=["Quiz"])
async def generate_quiz(request: QuizRequest) -> QuizResponse:
    """
    Generate MCQ quiz questions from an indexed document.

    Uses the first N chunks of the document as context (broad coverage),
    then instructs the LLM to produce questions in strict JSON format.
    """
    # ── 1. Verify collection ──────────────────────────────────────────────────
    if not collection_exists(request.collection_name):
        raise HTTPException(
            status_code=404,
            detail=f"Document '{request.collection_name}' not found. Upload it first.",
        )

    # ── 2. Get document context ───────────────────────────────────────────────
    # For quizzes we want broad document coverage, not a specific topic.
    # We take more chunks (up to 15) to give the LLM enough material to
    # generate diverse, non-repetitive questions.
    try:
        context = get_document_context(
            collection_name=request.collection_name,
            max_chunks=min(15, request.num_questions * 2),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {e}")

    # ── 3. Build prompt + call LLM ────────────────────────────────────────────
    user_prompt = build_quiz_prompt(context=context, num_questions=request.num_questions)

    try:
        raw_response = generate(
            user_prompt=user_prompt,
            system_prompt=QUIZ_SYSTEM_PROMPT,
            temperature=0.4,    # slight creativity for varied question phrasing
            max_tokens=4096,    # quizzes need more tokens (multiple questions)
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # ── 4. Parse + validate questions ─────────────────────────────────────────
    try:
        questions = _parse_quiz_response(raw_response, request.num_questions)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return QuizResponse(questions=questions)


@router.post("/evaluate-quiz", response_model=EvaluateResponse, tags=["Quiz"])
async def evaluate_quiz(request: EvaluateRequest) -> EvaluateResponse:
    """
    Score student answers against the correct answers.

    WHY a backend endpoint for evaluation?
      Keeps evaluation logic in one place. The frontend sends the
      questions (with correct answers) + student's choices, and
      gets back a structured results object — no scoring logic in the UI.
    """
    if len(request.questions) != len(request.answers):
        raise HTTPException(
            status_code=400,
            detail="Number of answers must match number of questions.",
        )

    results = []
    correct_count = 0

    for question, student_answer in zip(request.questions, request.answers):
        is_correct = student_answer.strip().upper() == question.correct_answer.strip().upper()
        if is_correct:
            correct_count += 1

        results.append({
            "question":        question.question,
            "student_answer":  student_answer,
            "correct_answer":  question.correct_answer,
            "is_correct":      is_correct,
            "explanation":     question.explanation,
            "options":         question.options,
        })

    total      = len(request.questions)
    percentage = round((correct_count / total) * 100, 1) if total > 0 else 0.0

    return EvaluateResponse(
        score=correct_count,
        total=total,
        percentage=percentage,
        results=results,
    )

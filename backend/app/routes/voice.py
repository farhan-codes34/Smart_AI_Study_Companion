"""
voice.py — POST /api/voice-query endpoint

Full pipeline:
  Audio file → Whisper STT → text question
  → embed → ChromaDB RAG retrieval
  → Groq LLM (grounded answer)
  → gTTS MP3
  → return transcription + answer text + audio URL

This endpoint reuses the exact same RAG + LLM logic as /api/ask,
just with audio input/output wrapped around it.
"""

from __future__ import annotations

import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.models.schemas import VoiceQueryResponse
from app.services.stt_service import transcribe_audio, save_upload_to_temp
from app.services.tts_service import text_to_speech, cleanup_old_audio
from app.services.rag_engine import retrieve_context, build_context_string
from app.services.vector_store import collection_exists
from app.services.llm_service import generate
from app.services.json_parser import extract_json
from app.prompts.qa_prompt import QA_SYSTEM_PROMPT, build_qa_prompt

router = APIRouter()


@router.post("/voice-query", response_model=VoiceQueryResponse, tags=["Voice"])
async def voice_query(
    collection_name: str  = Form(...),
    audio:           UploadFile = File(...),
) -> VoiceQueryResponse:
    """
    Full voice Q&A pipeline: audio in → text answer + MP3 audio out.

    Accepts multipart/form-data with:
      - collection_name: which ChromaDB document to query
      - audio: the recorded audio file (wav / webm / mp3)
    """
    # ── 1. Validate collection ────────────────────────────────────────────────
    if not collection_exists(collection_name):
        raise HTTPException(
            status_code=404,
            detail=f"Document '{collection_name}' not found. Upload it first.",
        )

    # ── 2. Save audio to temp file ────────────────────────────────────────────
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio file is empty.")

    # Preserve original extension so Whisper picks the right decoder
    original_name = audio.filename or "recording.wav"
    suffix = os.path.splitext(original_name)[1] or ".wav"
    temp_path = save_upload_to_temp(audio_bytes, suffix=suffix)

    # ── 3. Transcribe with Whisper ────────────────────────────────────────────
    try:
        question = transcribe_audio(temp_path)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        # Always clean up temp file, even if transcription failed
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # ── 4. RAG retrieval ──────────────────────────────────────────────────────
    try:
        chunks      = retrieve_context(collection_name, question, top_k=4)
        context_str = build_context_string(chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG retrieval failed: {e}")

    # ── 5. LLM — grounded answer ──────────────────────────────────────────────
    user_prompt = build_qa_prompt(context=context_str, question=question)

    try:
        raw_response = generate(
            user_prompt=user_prompt,
            system_prompt=QA_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=512,    # keep voice answers concise — shorter = clearer TTS
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    try:
        parsed = extract_json(raw_response)
        answer = parsed.get("answer", "").strip()
    except ValueError:
        # If JSON parse fails, use the raw text as the answer
        answer = raw_response.strip()

    if not answer:
        answer = "I could not find an answer in your notes. Please try again."

    # ── 6. Convert answer to speech ───────────────────────────────────────────
    try:
        audio_filename = text_to_speech(answer)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Keep audio folder tidy (max 20 files)
    cleanup_old_audio(keep_latest=20)

    return VoiceQueryResponse(
        transcribed_question=question,
        answer=answer,
        audio_filename=audio_filename,
    )

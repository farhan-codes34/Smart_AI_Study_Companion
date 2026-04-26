"""
stt_service.py — Speech-to-Text using Groq's Whisper API

Uses Groq's hosted whisper-large-v3-turbo model instead of running
whisper locally. This avoids loading a ~200MB model into RAM on startup,
which is critical for Render's free tier (512MB limit).
"""

from __future__ import annotations

import os
import tempfile
from groq import Groq
from app.config import settings


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe an audio file to text using Groq's Whisper API.

    Args:
        audio_path: Absolute path to the audio file.
                    Supported formats: wav, mp3, mp4, m4a, webm, ogg, flac.

    Returns:
        Transcribed text as a plain string.

    Raises:
        RuntimeError: If transcription fails.
    """
    if not os.path.exists(audio_path):
        raise RuntimeError(f"Audio file not found: {audio_path}")

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), audio_file.read()),
                model="whisper-large-v3-turbo",
                language="en",
            )
        text = transcription.text.strip()

        if not text:
            raise RuntimeError(
                "Whisper returned empty transcription. "
                "Ensure the audio contains clear speech."
            )
        return text

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}") from e


def save_upload_to_temp(audio_bytes: bytes, suffix: str = ".wav") -> str:
    """Save raw audio bytes to a named temporary file."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(audio_bytes)
    tmp.flush()
    tmp.close()
    return tmp.name

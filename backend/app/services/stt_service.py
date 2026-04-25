"""
stt_service.py — Speech-to-Text using OpenAI Whisper (core GenAI concept: STT)

WHY Whisper?
  Whisper is OpenAI's open-source speech recognition model. It runs
  100% locally — no API key, no internet required after first download.
  The "base" model (~140 MB) gives good accuracy for clear speech
  and is fast enough for real-time use on a CPU.

WHY local STT instead of a cloud API?
  - No cost per request
  - Works offline (important for students in areas with poor connectivity)
  - Privacy — audio never leaves the machine
  - No rate limits

Model sizes (accuracy vs speed trade-off):
  tiny   ~39 MB   fastest, lowest accuracy
  base   ~140 MB  good balance — default for this project
  small  ~460 MB  better accuracy, slower
  medium ~1.5 GB  high accuracy, much slower
  large  ~3 GB    best accuracy, very slow on CPU
"""

from __future__ import annotations

import os
import tempfile
import whisper

from app.config import settings

# ── Ensure ffmpeg is findable on Windows (WinGet install location) ────────────
def _ensure_ffmpeg_on_path() -> None:
    winget_base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages")
    if not os.path.isdir(winget_base):
        return
    for pkg_folder in os.listdir(winget_base):
        if pkg_folder.startswith("Gyan.FFmpeg"):
            pkg_path = os.path.join(winget_base, pkg_folder)
            for root, _dirs, files in os.walk(pkg_path):
                if "ffmpeg.exe" in files:
                    if root not in os.environ.get("PATH", ""):
                        os.environ["PATH"] = root + os.pathsep + os.environ.get("PATH", "")
                    return

_ensure_ffmpeg_on_path()

# ── Singleton model ───────────────────────────────────────────────────────────
_whisper_model: whisper.Whisper | None = None


def _get_model() -> whisper.Whisper:
    """Load Whisper model once and cache it for the process lifetime."""
    global _whisper_model
    if _whisper_model is None:
        print(f"⏳ Loading Whisper model '{settings.WHISPER_MODEL}'...")
        _whisper_model = whisper.load_model(settings.WHISPER_MODEL)
        print("✅ Whisper model loaded.")
    return _whisper_model


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe an audio file to text using Whisper.

    WHY fp16=False on Windows/CPU?
      fp16 (half-precision float) requires a CUDA GPU.
      On CPU or Windows without CUDA, fp16 causes a warning and
      falls back automatically — setting it False avoids the warning.

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
        model = _get_model()
        result = model.transcribe(
            audio_path,
            fp16=False,          # CPU-safe (no CUDA required)
            language="en",       # English — change to None for auto-detect
            verbose=False,       # suppress per-segment console output
        )
        text = result.get("text", "").strip()

        if not text:
            raise RuntimeError(
                "Whisper returned empty transcription. "
                "Ensure the audio contains clear speech."
            )

        return text

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}") from e


def save_upload_to_temp(audio_bytes: bytes, suffix: str = ".wav") -> str:
    """
    Save raw audio bytes to a named temporary file.

    WHY a named temp file?
      Whisper's transcribe() requires a file path, not in-memory bytes.
      NamedTemporaryFile with delete=False gives us a path we can pass
      to Whisper, and we delete the file manually afterwards.

    Args:
        audio_bytes: Raw audio content from the HTTP upload.
        suffix:      File extension (default .wav, matches browser recording).

    Returns:
        Absolute path to the saved temp file.
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(audio_bytes)
    tmp.flush()
    tmp.close()
    return tmp.name

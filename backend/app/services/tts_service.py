"""
tts_service.py — Text-to-Speech using gTTS (core GenAI concept: TTS)

WHY gTTS?
  Google Text-to-Speech (gTTS) converts text to natural-sounding MP3
  audio using Google's TTS API. It's free for reasonable usage, requires
  no API key, and produces better quality than offline alternatives.

  The trade-off: it requires an internet connection (unlike Whisper which
  runs fully locally). For a study tool deployed online this is acceptable.

Output:
  MP3 file saved to AUDIO_DIR, served as a static file by FastAPI.
  The frontend receives the filename and constructs the full URL.
"""

import os
import uuid
from gtts import gTTS, gTTSError

from app.config import settings


def text_to_speech(text: str) -> str:
    """
    Convert a text string to an MP3 audio file using gTTS.

    WHY UUID filename?
      Each answer generates a unique filename so multiple users or
      multiple queries don't overwrite each other's audio files.

    Args:
        text: The answer text to convert to speech.
              Long texts are handled automatically by gTTS.

    Returns:
        Filename of the generated MP3 (not the full path).
        The file lives in settings.AUDIO_DIR and is served at /audio/{filename}.

    Raises:
        RuntimeError: If TTS conversion fails (e.g. no internet, text too long).
    """
    if not text or not text.strip():
        raise RuntimeError("Cannot convert empty text to speech.")

    # Clean text for TTS — remove markdown formatting that sounds weird when spoken
    clean_text = _clean_for_tts(text)

    os.makedirs(settings.AUDIO_DIR, exist_ok=True)
    filename   = f"answer_{uuid.uuid4().hex[:12]}.mp3"
    output_path = os.path.join(settings.AUDIO_DIR, filename)

    try:
        tts = gTTS(text=clean_text, lang="en", slow=False)
        tts.save(output_path)
        return filename

    except gTTSError as e:
        raise RuntimeError(
            f"TTS generation failed: {e}. "
            "Check your internet connection — gTTS requires online access."
        ) from e
    except Exception as e:
        raise RuntimeError(f"TTS error: {e}") from e


def _clean_for_tts(text: str) -> str:
    """
    Strip markdown/formatting characters that sound bad when read aloud.

    Examples:
      "**important**"  → "important"
      "# Heading"      → "Heading"
      "`code`"         → "code"
    """
    import re
    # Remove bold/italic markers
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)
    # Remove heading markers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove inline code backticks
    text = re.sub(r"`(.+?)`", r"\1", text)
    # Remove escaped newlines from JSON
    text = text.replace("\\n", " ")
    # Collapse multiple spaces/newlines
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def cleanup_old_audio(keep_latest: int = 20) -> None:
    """
    Delete old audio files, keeping only the most recent N files.

    WHY cleanup?
      Each voice query generates a new MP3. Without cleanup the audio
      folder grows indefinitely. Keeping the latest 20 files is enough
      for any active session while preventing unbounded disk usage.

    Args:
        keep_latest: Number of most recent files to keep.
    """
    audio_dir = settings.AUDIO_DIR
    if not os.path.exists(audio_dir):
        return

    files = [
        os.path.join(audio_dir, f)
        for f in os.listdir(audio_dir)
        if f.endswith(".mp3")
    ]
    files.sort(key=os.path.getmtime, reverse=True)

    for old_file in files[keep_latest:]:
        try:
            os.remove(old_file)
        except OSError:
            pass

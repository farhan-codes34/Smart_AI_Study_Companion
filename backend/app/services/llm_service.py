"""
llm_service.py — Groq API wrapper (core GenAI concept: LLM via API)

WHY Groq?
  Groq runs Llama-3.3-70B on custom LPU hardware — it's free, extremely
  fast (~500 tokens/sec), and requires no GPU on our side. All the heavy
  computation happens on Groq's servers; we just send a prompt and get text.

WHY a wrapper module?
  Every feature (explain, quiz, Q&A) calls the LLM differently but through
  the same API. Centralising the Groq client here means:
    - One place to change the model or API key
    - Consistent error handling across all features
    - Easy to swap providers later (OpenAI, Anthropic, etc.)
"""

from __future__ import annotations

from groq import Groq, APIError, RateLimitError, APITimeoutError
from app.config import settings


# ── Singleton Groq client ─────────────────────────────────────────────────────
_client: Groq | None = None


def _get_client() -> Groq:
    """Return the shared Groq client, creating it on first call."""
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
            raise RuntimeError(
                "GROQ_API_KEY is not set. "
                "Add your key to backend/.env — get one free at https://console.groq.com"
            )
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def generate(
    user_prompt: str,
    system_prompt: str = "You are a helpful AI study tutor.",
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> str:
    """
    Send a prompt to the Groq LLM and return the text response.

    WHY temperature=0.3?
      Lower temperature = more focused, deterministic output.
      For educational content we want accurate explanations, not creativity.
      Quiz generation uses 0.4 (slightly more variety in questions).
      Voice Q&A uses 0.2 (most grounded, least creative).

    Args:
        user_prompt:   The main instruction + content to process.
        system_prompt: Sets the LLM's persona and constraints.
        temperature:   0.0 = deterministic, 1.0 = creative. Default 0.3.
        max_tokens:    Maximum tokens in the response.

    Returns:
        The LLM's text response as a plain string.

    Raises:
        RuntimeError: On API errors with a user-friendly message.
    """
    client = _get_client()

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    except RateLimitError:
        raise RuntimeError(
            "Groq rate limit reached. Wait a few seconds and try again. "
            "Free tier allows ~30 requests/minute."
        )
    except APITimeoutError:
        raise RuntimeError(
            "Groq API timed out. The model may be under heavy load — try again."
        )
    except APIError as e:
        raise RuntimeError(f"Groq API error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"LLM generation failed: {e}") from e

"""
json_parser.py — Robust JSON extraction from LLM responses

WHY this module exists:
  LLMs often return JSON with these common issues:
    1. Wrapped in markdown fences  (```json ... ```)
    2. Extra text before/after the JSON block
    3. Literal newlines inside string values (invalid JSON control chars)
       e.g. "explanation": "Line one.\n\nLine two."  ← raw \n is invalid
    4. Trailing commas, smart quotes, or other minor formatting quirks

  Standard json.loads() rejects all of the above. This module fixes
  each issue in sequence so parsing is reliable across LLM responses.

  Used by: explain.py, quiz.py, voice.py
"""

import json
import re


def _fix_control_chars_in_strings(text: str) -> str:
    """
    Replace literal control characters (newlines, tabs, carriage returns)
    that appear INSIDE JSON string values with their escaped equivalents.

    WHY character-by-character?
      A regex that blindly replaces all \n would also replace structural
      whitespace between JSON keys, making the JSON unparseable.
      By tracking whether we're inside a quoted string, we only escape
      control chars where JSON actually requires it.

    Example:
      Input:  {"key": "Hello\nWorld"}   ← raw newline inside string (INVALID)
      Output: {"key": "Hello\\nWorld"}  ← escaped (VALID JSON)
    """
    result   = []
    in_str   = False   # are we currently inside a JSON string?
    i        = 0
    n        = len(text)

    while i < n:
        ch = text[i]

        if ch == '\\' and in_str:
            # Escaped character — pass both chars through unchanged
            result.append(ch)
            i += 1
            if i < n:
                result.append(text[i])
            i += 1
            continue

        if ch == '"':
            in_str = not in_str
            result.append(ch)
            i += 1
            continue

        if in_str:
            # Inside a string — escape illegal control characters
            if ch == '\n':
                result.append('\\n')
            elif ch == '\r':
                result.append('\\r')
            elif ch == '\t':
                result.append('\\t')
            else:
                result.append(ch)
        else:
            result.append(ch)

        i += 1

    return ''.join(result)


def extract_json(text: str) -> dict:
    """
    Extract and parse a JSON object from raw LLM output.

    Steps applied in order:
      1. Strip markdown code fences
      2. Find the outermost { ... } boundaries
      3. Fix literal control characters inside string values
      4. Parse with json.loads

    Args:
        text: Raw string returned by the LLM.

    Returns:
        Parsed Python dict.

    Raises:
        ValueError: If no JSON object is found or parsing fails.
    """
    if not text:
        raise ValueError("LLM returned an empty response.")

    # Step 1 — strip markdown fences
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```\s*$",        "", text, flags=re.MULTILINE)
    text = text.strip()

    # Step 2 — find JSON object boundaries
    start = text.find("{")
    end   = text.rfind("}") + 1

    if start == -1 or end <= start:
        raise ValueError(
            "No JSON object found in LLM response. "
            f"Raw text (first 200 chars): {text[:200]}"
        )

    json_str = text[start:end]

    # Step 3 — try direct parse first (happy path)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Step 4 — fix control characters and retry
    json_str_fixed = _fix_control_chars_in_strings(json_str)

    try:
        return json.loads(json_str_fixed)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Could not parse LLM JSON after cleanup: {e}. "
            f"Cleaned JSON (first 300 chars): {json_str_fixed[:300]}"
        )

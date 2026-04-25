"""
explain_prompt.py — Prompt templates for the Explanation feature

WHY prompt engineering matters (core GenAI concept):
  The same LLM gives completely different quality answers depending on
  how you phrase the prompt. A well-engineered prompt:
    - Sets a clear PERSONA (expert tutor)
    - Constrains the output to the provided CONTEXT (prevents hallucination)
    - Specifies exact OUTPUT FORMAT (JSON for reliable parsing)
    - Gives EXAMPLES of the tone and depth expected

Key design decisions in these prompts:
  1. "ONLY use the content provided" — grounds the LLM in the document
  2. Strict JSON format — makes parsing the response reliable
  3. Separate system/user messages — system sets persona, user gives the task
"""


EXPLAIN_SYSTEM_PROMPT = """You are an expert AI study tutor. Your role is to help students
understand their lecture notes and textbook material.

STRICT RULES you must follow:
1. ONLY use information from the content provided in the user message.
2. Do NOT add facts, examples, or explanations from your training data.
3. If the content is insufficient, say so in the explanation field.
4. Always respond with valid JSON — no extra text before or after the JSON block.
5. Write as if explaining to a smart high school or first-year university student.
6. CRITICAL — JSON formatting: All string values must be on a single line.
   Use the literal two characters backslash-n (\\n) to separate paragraphs inside
   a JSON string. NEVER put a raw line break inside a JSON string value."""


def build_explain_prompt(context: str, topic: str | None = None) -> str:
    """
    Build the user-facing prompt for explanation generation.

    Args:
        context: The retrieved document chunks (formatted by build_context_string).
        topic:   Optional focus topic from the user (e.g. "photosynthesis").
                 If None, explain the overall document content.

    Returns:
        A formatted prompt string ready to send to the LLM.
    """
    if topic and topic.strip():
        topic_line = (
            f"The student wants to understand specifically: **{topic.strip()}**\n"
            "Focus your explanation on that topic as found in the content."
        )
    else:
        topic_line = (
            "The student wants a general explanation of the content above.\n"
            "Cover the main ideas and key concepts."
        )

    return f"""Here is the study material content retrieved from the student's notes:

<content>
{context}
</content>

{topic_line}

Respond ONLY with this exact JSON structure. Do not include any text outside the JSON:

{{
    "explanation": "Write a clear explanation in 3 to 5 short paragraphs. Use simple everyday language. Avoid jargon or define it when used.",
    "key_points": [
        "First key point — one sentence",
        "Second key point — one sentence",
        "Third key point — one sentence",
        "Fourth key point — one sentence",
        "Fifth key point — one sentence"
    ],
    "analogy": "One memorable real-life analogy that connects this concept to something a student already knows from daily life."
}}"""

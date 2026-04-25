"""
qa_prompt.py — Prompt templates for RAG-based Q&A

WHY strict grounding matters (core GenAI concept: context-grounded generation):
  Without grounding, the LLM answers from its training data — which may be
  outdated, generic, or simply wrong for the student's specific notes.

  This prompt uses two techniques to prevent hallucination:
    1. CONTEXT INJECTION — the retrieved chunks are placed directly in the prompt
    2. EXPLICIT CONSTRAINT — the system prompt forbids answers outside context

  If the answer isn't in the student's notes, the LLM says so honestly.
  This is more useful than a confident wrong answer.
"""


QA_SYSTEM_PROMPT = """You are a precise AI study assistant. You answer student questions
based STRICTLY on the provided context from their uploaded notes.

STRICT RULES:
1. Answer ONLY using information found in the CONTEXT section below.
2. If the answer is not in the context, respond with:
   "I could not find information about this in your notes. Try uploading more relevant material."
3. Do NOT use your training data or general knowledge to fill gaps.
4. Be concise and clear — 2 to 4 sentences unless the question requires more detail.
5. If the context partially answers the question, share what IS there and note what is missing.
6. CRITICAL — JSON formatting: All string values must be on a single line.
   Use the literal two characters backslash-n (\\n) to separate paragraphs.
   NEVER put a raw line break inside a JSON string value."""


def build_qa_prompt(context: str, question: str) -> str:
    """
    Build the user-facing prompt for a RAG Q&A turn.

    Args:
        context:  Formatted string of retrieved document chunks.
        question: The student's question (text or transcribed from voice).

    Returns:
        Formatted prompt string ready to send to the LLM.
    """
    return f"""Use the following context from the student's uploaded notes to answer the question.

<context>
{context}
</context>

Student's question: {question}

Respond ONLY with this exact JSON structure (no extra text outside the JSON):
{{
    "answer": "Your clear, concise answer based only on the context above.",
    "found_in_notes": true,
    "confidence": "high"
}}

If the answer is NOT in the context:
{{
    "answer": "I could not find information about this in your notes. Try uploading more relevant material or rephrasing your question.",
    "found_in_notes": false,
    "confidence": "none"
}}"""

"""
quiz_prompt.py — Prompt templates for MCQ quiz generation

WHY structured output (core GenAI concept):
  Unstructured LLM output is hard to display in a UI. By instructing the
  LLM to return strict JSON, we can reliably parse it into Python objects
  and build an interactive quiz without fragile string manipulation.

  Key prompt engineering decisions:
    1. Provide a clear JSON schema with an example — LLMs follow examples
       better than abstract descriptions
    2. Set difficulty to "moderate" — too easy/hard defeats the purpose
    3. Use options with letter prefixes (A/B/C/D) to make answer
       comparison straightforward
    4. Ask for an explanation per question — students learn from mistakes
    5. Forbid reusing the same answer letter repeatedly — prevents bias
"""


QUIZ_SYSTEM_PROMPT = """You are an expert quiz generator for students.
Your job is to create high-quality multiple-choice questions (MCQs) from study material.

STRICT RULES:
1. Generate questions ONLY from the provided content — no outside knowledge.
2. Each question must have exactly 4 options labeled A, B, C, D.
3. correct_answer must be exactly one of: "A", "B", "C", or "D".
4. Make questions moderately challenging — test understanding, not just memorization.
5. Vary the correct answer position (don't always make A or B correct).
6. Each explanation must state WHY the correct answer is right.
7. CRITICAL — JSON formatting: All string values must be on a single line.
   Use backslash-n (\\n) if you need line breaks inside strings.
   NEVER put a raw line break inside a JSON string value.
8. Return ONLY the JSON object — no extra text before or after."""


def build_quiz_prompt(context: str, num_questions: int) -> str:
    """
    Build the prompt for quiz generation.

    Args:
        context:       Formatted document chunks to generate questions from.
        num_questions: How many MCQs to generate (1–20).

    Returns:
        Formatted prompt string ready for the LLM.
    """
    return f"""Here is the study material content:

<content>
{context}
</content>

Generate exactly {num_questions} multiple-choice question(s) from the content above.

Return ONLY this exact JSON structure — no text outside the JSON:

{{
    "questions": [
        {{
            "question": "Clear, specific question about the content?",
            "options": [
                "A. First option",
                "B. Second option",
                "C. Third option",
                "D. Fourth option"
            ],
            "correct_answer": "B",
            "explanation": "B is correct because [reason from the content]. The other options are incorrect because [brief reason]."
        }}
    ]
}}

Requirements:
- Generate exactly {num_questions} question(s)
- Each question tests a different concept from the content
- All 4 options must be plausible (avoid obviously wrong distractors)
- correct_answer must be exactly "A", "B", "C", or "D" (capital letter only)"""

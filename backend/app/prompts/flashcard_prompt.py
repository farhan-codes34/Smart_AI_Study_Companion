"""
flashcard_prompt.py — Prompt templates for flashcard generation

WHY flashcards (GenAI concept extension):
  Flashcards are one of the most proven study techniques (spaced repetition).
  By instructing the LLM to extract key term-definition pairs from the document,
  we add a new study mode that complements the quiz feature.

  Prompt engineering decisions:
    1. Ask for TERM (concise, front of card) + DEFINITION (1-3 sentences, back)
    2. Strict JSON schema with example — LLMs follow examples reliably
    3. Forbid vague terms — forces the model to pick specific, useful concepts
    4. Cap definition length — cards should be scannable, not paragraphs
    5. ONLY from provided context — grounded generation, no hallucination
"""

FLASHCARD_SYSTEM_PROMPT = """You are an expert study assistant that creates concise, effective flashcards.
Your job is to identify the most important concepts in study material and turn them into clear flashcards.

STRICT RULES:
1. Extract terms ONLY from the provided content — no outside knowledge.
2. Each term must be a specific concept, key vocabulary word, formula, or named idea.
3. Definitions must be 1–3 sentences maximum — concise and scannable.
4. Do NOT use vague terms like "important concept" or "key idea".
5. Cover a broad range of topics from the document (don't repeat similar concepts).
6. CRITICAL — JSON formatting: All string values must be on a single line.
   Use backslash-n (\\n) if you need line breaks inside strings.
   NEVER put a raw line break inside a JSON string value.
7. Return ONLY the JSON object — no extra text before or after."""


def build_flashcard_prompt(context: str, num_cards: int) -> str:
    """
    Build the prompt for flashcard generation.

    Args:
        context:   Formatted document chunks to extract flashcards from.
        num_cards: How many flashcards to generate (5–30).

    Returns:
        Formatted prompt string ready for the LLM.
    """
    return f"""Here is the study material content:

<content>
{context}
</content>

Generate exactly {num_cards} flashcard(s) from the content above.

Return ONLY this exact JSON structure — no text outside the JSON:

{{
    "flashcards": [
        {{
            "term": "Photosynthesis",
            "definition": "The process by which green plants use sunlight, water, and carbon dioxide to produce glucose and oxygen. It takes place primarily in the chloroplasts of plant cells."
        }}
    ]
}}

Requirements:
- Generate exactly {num_cards} flashcard(s)
- Each term should be a distinct concept from the document
- Definitions must be 1–3 sentences, clear and exam-ready
- Cover as many different topics from the document as possible
- Terms should be specific (e.g. "Mitochondria" not "Cell part")
- Do NOT duplicate or paraphrase the same concept twice"""

"""
service.py
Coordinates prompt generation, Gemini API interactions, and error handling.
"""

from core.llm.client import client, MODEL
from core.llm.citation_prompt import build_auditor_prompt


def generate_audited_response(question: str, evidence: list[dict]) -> tuple[str, str]:
    """
    Generates a cited financial auditor response for the question given retrieved evidence chunks.
    Returns (answer_text, formatted_prompt).
    """
    prompt = build_auditor_prompt(question, evidence)

    if client is None:
        answer = (
            f"[GEMINI_API_KEY NOT SET]\n"
            f"Retrieved {len(evidence)} high-relevance evidence chunks via Hybrid Search.\n"
            f"To generate the final LLM response, add your GEMINI_API_KEY to .env."
        )
        return answer, prompt

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
        answer = response.text.strip() if response.text else "No response generated."
        return answer, prompt

    except Exception as e:
        answer = f"Gemini Generation Error: {e} (Retrieved {len(evidence)} evidence chunks)."
        return answer, prompt
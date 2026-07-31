# becomes the bridge between prompts and the client

from core.llm.prompts import build_answer_prompt
from core.llm.client import client, MODEL

def generate_answer(question: str) -> str | None:
    try:
        prompt = build_answer_prompt(question)
        
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        if not response.text:
            raise RuntimeError("Empty response from Gemini.")
        return response.text.strip()
    
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None
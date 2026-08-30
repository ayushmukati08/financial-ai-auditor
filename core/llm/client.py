# This file should have the responsibility to create and expose the Gemini client.

from google import genai
from core.config import GEMINI_API_KEY, GEMINI_MODEL

# Load API key from .env
MODEL = GEMINI_MODEL

def get_gemini_client(api_key: str = GEMINI_API_KEY) -> genai.Client | None:
    """
    Returns a configured Gemini client, or None if GEMINI_API_KEY is not set.
    """
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


client = get_gemini_client()
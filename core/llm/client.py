# This file should have the responsibility to create and expose the Gemini client.

import os
from dotenv import load_dotenv
from google import genai

# Load API key from .env
load_dotenv()

API_KEY=os.getenv("GEMINI_API_KEY")
MODEL=os.getenv("GEMINI_MODEL")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

if not MODEL:
    raise ValueError("GEMINI_MODEL not found")

client = genai.Client(api_key=API_KEY)
# app/llm/client.py
from app.core.logger import logger
import os
import json
from app.core.config import settings
from google import genai



GEMINI_KEY = (
    os.getenv("GEMINI_API_KEY")
    or getattr(settings, "gemini_api_key", None)
)

GEMINI_MODEL = (
    os.getenv("GEMINI_MODEL")
    or getattr(settings, "gemini_model_name", None)
    or "gemini-2.0-flash"
)


# app/llm/client.py

# ... imports remain the same ...

def ask_llm(prompt: str, max_tokens: int = 500, temperature: float = 0.2) -> str:

    if genai is None:
        raise RuntimeError("google-genai SDK not installed. Please run: pip install google-genai")
    
    if not GEMINI_KEY:
        raise RuntimeError("GEMINI_API_KEY not set.")

    try:
        # FIX 1: Pass api_key directly to Client. Do NOT use genai.configure()
        client = genai.Client(api_key=GEMINI_KEY)

        # FIX 2: The new SDK expects config parameters (temp, tokens) in a 'config' dictionary
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                'temperature': temperature,
                'max_output_tokens': max_tokens
            }
        )

        # FIX 3: The new SDK response object text attribute access
        output = response.text
        
        if not output:
            raise RuntimeError(f"Gemini returned no text. Raw: {response}")
        return output

    except Exception as e:
        logger.error("[LLM CLIENT] ERROR DURING GEMINI CALL: %s", e)
        raise

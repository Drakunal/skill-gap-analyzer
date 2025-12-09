# app/services/extractor_service.py
import json
from app.llm.client import ask_llm
from app.llm.prompts import EXTRACT_SKILLS_PROMPT
from app.models.schemas import normalize_skill_name

def extract_skills_from_text(text: str):
    """
    Ask the LLM to extract skills from the provided text.
    Returns a list of normalized skill names (title-cased).
    Uses a JSON-output-first strategy with a simple fallback.
    """
    prompt = EXTRACT_SKILLS_PROMPT.replace('{TEXT}', text[:4000])
    resp = ask_llm(prompt)
    skills = []
    # Try parse LLM response as JSON first
    try:
        parsed = json.loads(resp)
        if isinstance(parsed, dict):
            # accept both keys "skills" and "skill"
            skills = parsed.get('skills') or parsed.get('skill') or []
        elif isinstance(parsed, list):
            skills = parsed
    except Exception:
        # fallback: simple heuristic: pick common tech tokens and capitalized words
        tokens = set()
        low = text.lower()
        candidates = ['python','docker','sql','tensorflow','pytorch','fastapi','flask','aws','gcp','kubernetes','ci/cd','pandas','numpy','spark']
        for cand in candidates:
            if cand in low:
                tokens.add(cand)
        # also include capitalized words (basic)
        for word in text.split():
            w = word.strip('.,()[]:')
            if len(w) > 1 and w[0].isupper() and w.isalpha():
                tokens.add(w.lower())
        skills = list(tokens)
    # normalize and return
    return [normalize_skill_name(s) for s in skills]

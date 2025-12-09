Skill Gap Analyzer (Compact, no-RAG)
===================================

How to run (dev/demo):
1. python -m venv .venv
2. source .venv/bin/activate
3. pip install -r requirements.txt
4. Optional: create a .env file with OPENAI_API_KEY
5. ./run.sh
6. Endpoints:
   - POST /upload-jd   (json: {"job_description": "..."})
   - POST /upload-cv   (multipart file)
   - POST /analyze     (json: {"job_description": "...", "cv_id": "..."} or use uploaded ids)
   - POST /recommend   (json: {"missing_skills": [...]})
Demo works without OPENAI_API_KEY using deterministic fallback responses.

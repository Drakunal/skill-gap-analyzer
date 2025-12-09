EXTRACT_SKILLS_PROMPT = """Extract technical skills and keywords from the text below.
Return a JSON object exactly like:
{ "skills": ["skill1","skill2"], "keywords": ["k1","k2"] }
Text:
{TEXT}
"""

ANALYZE_PROMPT_TEMPLATE = """
You are an expert career assistant. Given the job description (JD) and a candidate CV text,
produce a JSON object ONLY (no extra commentary) with the following exact fields:

{
  "required_skills": ["..."],
  "cv_skills": ["..."],
  "missing_skills": ["..."],
  "matched_keywords": [ ... ],
  "suitability": { "score": 0.0, "label": "Strong Fit|Potential Fit|Not a Fit" },
  "difficulty_estimate": { "score": 0.0, "reason": "..." },
  "suggested_improvements": [ /* short project/keyword suggestions ok */ ],
  "confidence": 0.0,
  "flags": { "jd_malformed": false }
}

Rules:
- Output MUST be valid JSON only.
- Only extract skills explicitly present in the JD.
- If JD non-technical or too short, return required_skills: [] and set flags.jd_malformed true.
JD:
{JD}

CV:
{CV}
"""

CAREER_SUGGEST_PROMPT = """
You are a practical career advisor. Given a short job description (JD) and a candidate CV summary,
produce a JSON array (no extra text) of up to 3 actionable, realistic recommendations for the candidate
to move into the role described by the JD or to improve their fit. Each recommendation must contain:

{
 "title": "Short title for suggestion",
 "description": "1-2 sentence realistic plan with steps and expected duration",
 "cv_bullet": "One CV bullet the candidate can add after doing this (1 line)",
 "priority": "high|medium|low",
 "resources": ["link or resource title", ...]   // up to 3
}

Be conservative and realistic: include time estimates (e.g., 2-6 weeks), suggested small projects,
and where to learn (free docs/courses). Respond only with JSON array.
JD:
{JD}

CV (short):
{CV}
"""

READABLE_POLISH_PROMPT = """
Rewrite the following list of short recommendations into a coherent, human-friendly 2-4 paragraph advisory note
suitable for an applicant who is considering a career transition. Keep it personal, practical and actionable.
Do not invent new recommendations; rewrite only what is provided. Output plain text only.
Recommendations (JSON array):
{RECS}
"""

# Optional: small RECOMMEND_PROMPT used by recommend_service if expected
RECOMMEND_PROMPT = """
You are a practical coding/learning advisor. Given a missing skill name (keyword) produce a compact recommendation
object (no markup, plain JSON) with keys: project (short project title), cv_bullet (one-line bullet to add to CV),
resources (list of up to 3 resource titles or links). Example output:

{
  "project": "Build a simple portfolio website with 5 projects",
  "cv_bullet": "Built a portfolio website showcasing 5 projects including X, Y, Z",
  "resources": ["freecodecamp.org", "mdn web docs", "github pages tutorial"]
}

Only output the JSON object for the single skill provided.
"""

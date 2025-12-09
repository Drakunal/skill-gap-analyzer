# app/models/schemas.py
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
import re

# --- Input models ---

class UploadJDIn(BaseModel):
    job_description: str = Field(..., example="We need a ML engineer with Python, Docker, SQL")

class UploadCVOut(BaseModel):
    cv_id: str
    snippet: str
    cached: bool

class AnalyzeIn(BaseModel):
    job_description: str = Field(..., example="We need an ML engineer with Python, Docker, SQL")
    cv_id: str = Field(..., example="md5-checksum-of-cv")

    @model_validator(mode="after")
    def check_inputs(self):
        if not self.job_description or not self.cv_id:
            raise ValueError("Both job_description and cv_id are required.")
        return self

class RecommendIn(BaseModel):
    missing_skills: List[str]

# --- Shared small output models ---

class KeywordMatch(BaseModel):
    keyword: str
    occurrences_in_jd: int
    occurrences_in_cv: int
    context_jd: List[str] = []

class Suitability(BaseModel):
    score: float
    label: str

class Difficulty(BaseModel):
    score: float
    reason: str

class Improvement(BaseModel):
    type: str
    title: Optional[str] = None
    description: Optional[str] = None
    keyword: Optional[str] = None
    suggestion: Optional[str] = None
    priority: Optional[str] = None
    resources: Optional[List[str]] = None

# --- Final analyze response model ---

class AnalyzeOut(BaseModel):
    job_id: Optional[str]
    cv_id: Optional[str]
    jd_text_snippet: str
    cv_text_snippet: str
    required_skills: List[str]
    cv_skills: List[str]
    missing_skills: List[str]
    matched_keywords: List[KeywordMatch]
    suitability: Suitability
    difficulty_estimate: Difficulty
    suggested_improvements: List[Improvement]
    confidence: float
    flags: dict
    timing: dict

class RecommendOut(BaseModel):
    skill: str
    project: str
    resources: List[str]
    cv_bullet: str

# --- utility normalizer used by extraction function(s) ---

# replace the old normalize_skill_name with this safe version
def normalize_skill_name(s: str) -> str:
    """
    Normalize a skill token to a readable Title case.
    - Removes punctuation except + # - (kept)
    - Lowercases, maps small synonyms, then Title-cases for display.
    """
    if not s:
        return s
    # allow letters, numbers, plus, hash, hyphen and spaces
    s2 = re.sub(r'[^A-Za-z0-9\+\#\-\s]+', '', str(s)).strip().lower()
    mapping = {'py': 'python', 'js': 'javascript', 'tf': 'tensorflow'}
    return mapping.get(s2, s2).title()


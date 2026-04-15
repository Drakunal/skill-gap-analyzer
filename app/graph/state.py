"""
LangGraph shared state for the Skill Gap Analyzer pipeline.

Design decisions:
- TypedDict (not Pydantic BaseModel) at the top level: LangGraph's StateGraph
  works best with TypedDict for the outer schema. Pydantic models are used for
  nested structured outputs (cv_profile, jd_requirements, etc.) because they
  give us validation + .model_dump() for free.

- Reducers: only `suggested_improvements` gets operator.add because both
  gap_analyst and coach append to it. Every other field is written by exactly
  one node, so the default "last write wins" is correct and safe.

- Optional fields default to None: nodes write only the keys they own.
  A node that doesn't return a key leaves it unchanged in state — LangGraph
  merges partial dicts, it does NOT reset unmentioned keys to None.
"""

import operator
from typing import Annotated, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-models: structured outputs from individual agents
# These are what each node produces and writes into state.
# ---------------------------------------------------------------------------

class CVProfile(BaseModel):
    """Structured CV output from cv_parser_agent."""
    raw_text: str = ""
    name: Optional[str] = None
    years_of_experience: Optional[float] = None
    current_role: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    past_roles: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    # parse_errors lets us degrade gracefully if LLM returns partial JSON
    parse_errors: list[str] = Field(default_factory=list)


class JDRequirements(BaseModel):
    """Structured JD output from jd_analyst_agent."""
    raw_text: str = ""
    job_title: Optional[str] = None
    seniority_level: Optional[str] = None   # "junior" | "mid" | "senior" | "lead"
    domain: Optional[str] = None            # "fintech" | "insurtech" | "ml-platform" etc.
    must_have_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    is_malformed: bool = False              # gate flag — True routes to error_node
    malformed_reason: Optional[str] = None


class GapAnalysis(BaseModel):
    """Output from gap_analyst_agent."""
    required_skills: list[str] = Field(default_factory=list)
    cv_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    matched_keywords: list[dict] = Field(default_factory=list)
    suitability_score: float = 0.0
    suitability_label: str = "Unknown"     # "Strong Fit" | "Potential Fit" | "Not a Fit"
    difficulty_score: float = 0.5
    difficulty_reason: str = ""
    confidence: float = 0.0


class CoachingPlan(BaseModel):
    """Output from coach_agent."""
    recommendations: list[dict] = Field(default_factory=list)
    cv_bullets: list[str] = Field(default_factory=list)
    cover_letter_draft: str = ""
    plan_quality_score: float = 0.0        # 0–1; if < threshold, coach loops
    retry_count: int = 0                   # guards against infinite loop


# ---------------------------------------------------------------------------
# Pipeline-level error tracking
# ---------------------------------------------------------------------------

class PipelineError(BaseModel):
    node: str
    message: str
    recoverable: bool = True


# ---------------------------------------------------------------------------
# The shared state TypedDict
# This is the "whiteboard" every node reads from and writes to.
# ---------------------------------------------------------------------------

class SkillGapState(TypedDict):
    # ── Inputs (set once by the API layer before graph.invoke()) ──────────
    cv_id: str                          # md5 checksum from your existing cache
    cv_raw_text: str                    # full extracted CV text
    jd_raw_text: str                    # raw job description text

    # ── Agent outputs (each node owns exactly one of these) ───────────────
    cv_profile: Optional[CVProfile]     # written by: cv_parser_agent
    jd_requirements: Optional[JDRequirements]  # written by: jd_analyst_agent
    gap_analysis: Optional[GapAnalysis]        # written by: gap_analyst_agent
    coaching_plan: Optional[CoachingPlan]      # written by: coach_agent

    # ── Accumulated list (reducer needed — gap_analyst + coach both write) ─
    suggested_improvements: Annotated[list[dict], operator.add]

    # ── Control flow flags (read by routing functions in edges/routing.py) ─
    jd_is_malformed: bool               # set by jd_analyst_agent; read by jd_quality_gate
    coach_retry_count: int              # incremented by coach_agent on weak plans
    pipeline_complete: bool             # set True by coach_agent when plan is good

    # ── Error tracking ────────────────────────────────────────────────────
    errors: Annotated[list[PipelineError], operator.add]  # any node can append

    # ── Timing / metadata (for observability) ─────────────────────────────
    run_id: Optional[str]
    timing: dict                        # node_name → duration_ms
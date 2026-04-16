"""
Routing functions for conditional edges.

Rules:
- Every function takes `state: SkillGapState` and returns a string
  (or list of strings for fan-out).
- They must be pure: no side effects, no LLM calls, no I/O.
- Return values must exactly match node names registered in builder.py.
  A typo here causes a silent mis-route at runtime — LangGraph won't error.
"""

from typing import Literal
from app.graph.state import SkillGapState

# Maximum coaching retries before we accept the plan as-is
MAX_COACH_RETRIES = 2
# Minimum quality score for coaching plan to be accepted
COACH_QUALITY_THRESHOLD = 0.6


def route_after_jd_gate(
    state: SkillGapState,
) -> Literal["gap_analyst_agent", "error_node"]:
    """
    Called after jd_quality_gate node runs.

    The jd_analyst_agent sets state["jd_is_malformed"] = True if the JD
    is too short, nonsensical, or not a job description at all.
    We read that flag and route accordingly.
    """
    if state.get("jd_is_malformed", False):
        return "error_node"
    return "gap_analyst_agent"

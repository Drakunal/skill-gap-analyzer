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


def route_after_coach(
    state: SkillGapState,
) -> Literal["gap_analyst_agent", "__end__"]:
    """
    Called after coach_agent runs.

    If the coaching plan quality is below threshold AND we haven't exceeded
    max retries, loop back to gap_analyst_agent so it can re-run with
    the coach's feedback written into state.

    Why loop back to gap_analyst rather than coach itself?
    Because a weak plan usually means the gap analysis was incomplete —
    re-running the coach on the same gap data would produce the same weak
    plan. Re-running gap analysis forces a fresh LLM pass on the underlying data.

    "__end__" is LangGraph's built-in sentinel — equivalent to importing END.
    Using the string literal avoids a circular import here.
    """
    plan = state.get("coaching_plan")
    retry_count = state.get("coach_retry_count", 0)

    if plan is None:
        # No plan was produced at all — don't loop forever
        return "__end__"

    if plan.plan_quality_score < COACH_QUALITY_THRESHOLD and retry_count < MAX_COACH_RETRIES:
        return "gap_analyst_agent"

    return "__end__"
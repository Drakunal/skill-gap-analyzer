# app/graph/nodes/coach_node.py
"""
Coach Agent node.

Responsibility: reads gap_analysis + cv_profile + jd_requirements,
generates learning plan, CV bullets, cover letter draft.
Sets plan_quality_score — this is what route_after_coach reads.

The retry loop: if quality < threshold, route_after_coach sends execution
back to gap_analyst_agent. coach_retry_count is incremented here so
routing.py can cap the loop at MAX_COACH_RETRIES.
"""

from app.graph.state import SkillGapState, CoachingPlan
from app.core.logger import logger


def coach_agent(state: SkillGapState) -> dict:
    retry_count = state.get("coach_retry_count", 0)
    logger.info("[coach_agent] Starting. retry=%d", retry_count)

    # STUB
    plan = CoachingPlan(
        recommendations=[],
        cv_bullets=[],
        cover_letter_draft="",
        plan_quality_score=0.7,  # stub: above threshold so loop doesn't fire
        retry_count=retry_count + 1,
    )

    logger.info("[coach_agent] Done. quality=%.2f", plan.plan_quality_score)
    # return {
    #     "coaching_plan": plan,
    #     "coach_retry_count": retry_count + 1,
    #     "suggested_improvements": [],   # operator.add accumulates
    #     "pipeline_complete": plan.plan_quality_score >= 0.6,
    # }
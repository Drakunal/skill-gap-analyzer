# app/graph/nodes/gap_analyst_node.py
"""
Gap Analyst Agent node.

Reuse decision: your existing compare_service.analyze_gap_and_keywords()
does deterministic gap analysis (set intersection, regex keyword counting).
We KEEP that as a fallback / fast path. This node adds an LLM pass on top
for richer semantic matching (e.g. "FastAPI" matching "REST API experience").
"""

from app.graph.state import SkillGapState, GapAnalysis
from app.core.logger import logger


def gap_analyst_agent(state: SkillGapState) -> dict:
    logger.info("[gap_analyst_agent] Starting. retry=%d", state.get("coach_retry_count", 0))

    # STUB
    analysis = GapAnalysis(
        required_skills=[],
        cv_skills=[],
        missing_skills=[],
        suitability_score=0.0,
        suitability_label="Unknown",
        confidence=0.0,
    )

    logger.info("[gap_analyst_agent] Done.")
    return {
        "gap_analysis": analysis,
        "suggested_improvements": [],   # operator.add will append, not overwrite
    }
# app/graph/nodes/jd_analyst_node.py
"""
JD Analyst Agent node.

Responsibility: takes jd_raw_text, extracts structured requirements,
detects seniority/domain/must-haves, sets jd_is_malformed flag.

The malformed flag is what the jd_quality_gate conditional edge reads.
If we detect the JD is garbage (< 30 words, no skill mentions, etc.)
we set it here so the routing function can divert cleanly.
"""

from app.graph.state import SkillGapState, JDRequirements
from app.core.logger import logger


def jd_analyst_agent(state: SkillGapState) -> dict:
    logger.info("[jd_analyst_agent] Starting. jd_len=%d", len(state.get("jd_raw_text", "")))

    # STUB — real implementation comes in Phase 2
    jd_text = state.get("jd_raw_text", "")

    # Basic malformed heuristic (will be replaced by LLM detection)
    is_malformed = len(jd_text.strip().split()) < 20
    reason = "JD too short (< 20 words)" if is_malformed else None

    requirements = JDRequirements(
        raw_text=jd_text,
        is_malformed=is_malformed,
        malformed_reason=reason,
    )

    logger.info("[jd_analyst_agent] Done. is_malformed=%s", is_malformed)

    return {
        "jd_requirements": requirements,
        "jd_is_malformed": is_malformed,   # write the control flag too
    }
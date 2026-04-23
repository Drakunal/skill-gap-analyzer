# app/graph/nodes/error_node.py
"""
Error node — terminal node for malformed JD or unrecoverable failures.

Writes a structured error into state and sets pipeline_complete=True
so the caller gets a clean response rather than a KeyError on missing fields.
"""

from app.graph.state import SkillGapState, PipelineError
from app.core.logger import logger


def error_node(state: SkillGapState) -> dict:
    jd_req = state.get("jd_requirements")
    reason = (jd_req.malformed_reason if jd_req else None) or "Unknown error"

    logger.warning("[error_node] Pipeline terminated. reason=%s", reason)

    error = PipelineError(
        node="jd_analyst_agent",
        message=reason,
        recoverable=False,
    )
    return {
        "errors": [error],
        "pipeline_complete": True,
    }
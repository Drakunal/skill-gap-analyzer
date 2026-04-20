"""
CV Parser Agent node.

Responsibility: takes cv_raw_text from state, calls LLM (or existing
parser_service) to extract a structured CVProfile, writes it back to state.

Reuse decision: your existing parse_and_cache_bytes() in parser_service.py
handles PDF/DOCX → raw text extraction. We DO NOT rewrite that. This node
sits *after* that — it takes the already-extracted raw text and runs a second
LLM pass to produce structured fields (skills, roles, education).
"""

from app.graph.state import SkillGapState, CVProfile
from app.core.logger import logger


def cv_parser_agent(state: SkillGapState) -> dict:
    """
    Node function signature: receives full state, returns partial update dict.
    LangGraph merges this dict into state — keys not in the return dict
    are left untouched.
    """
    logger.info("[cv_parser_agent] Starting. cv_id=%s", state.get("cv_id"))

    # STUB — real implementation comes in Phase 2
    # Will call: ask_llm(CV_PROFILE_EXTRACTION_PROMPT.format(cv_text=...))
    # Then parse JSON response into CVProfile

    profile = CVProfile(
        raw_text=state.get("cv_raw_text", ""),
        skills=[],          # placeholder
        parse_errors=["stub: not yet implemented"],
    )

    # logger.info("[cv_parser_agent] Done. skills_found=%d", len(profile.skills))

    # # Return ONLY the keys this node owns.
    # # Never return the full state — partial updates are the contract.
    return {"cv_profile": profile}
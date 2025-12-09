# app/services/analyze_service.py
"""
LLM-driven analyze + recommend service with human-readable outputs and logging.

Prompts are loaded from app.core.prompts.
Logging uses app.core.logger so all messages go to daily log files.
"""

import time
import json
import re
from typing import Dict, Any, List, Optional

from app.core.logger import logger
from app.llm.prompts import (
    ANALYZE_PROMPT_TEMPLATE,
    CAREER_SUGGEST_PROMPT,
    READABLE_POLISH_PROMPT,
)
from app.llm.client import ask_llm
from app.services.compare_service import analyze_gap_and_keywords
from app.services.recommend_service import recommend_for_skills
from app.services.extractor_service import extract_skills_from_text

# Configuration
MAX_CTX_CHARS = 16000
ANALYZE_MAX_TOKENS = 3000
CAREER_SUGGEST_MAX_TOKENS = 1200

# If True, the service will call the LLM to rewrite/polish the human-readable output.
# Disabled by default to avoid extra cost; you can flip for nicer prose.
try_llm_for_readable = False


def _safe_trim_text(t: str, n: int) -> str:
    if not t:
        return ""
    return t[:n]


def _occurrences_of_keyword_in_text(keyword: str, text: str) -> int:
    if not keyword or not text:
        return 0
    return len(re.findall(r"\b" + re.escape(keyword) + r"\b", text, flags=re.IGNORECASE))


def _llm_call_analyze(jd_text: str, cv_text: str) -> Optional[Dict[str, Any]]:
    jd_ctx = _safe_trim_text(jd_text, MAX_CTX_CHARS)
    cv_ctx = _safe_trim_text(cv_text, MAX_CTX_CHARS)
    prompt = ANALYZE_PROMPT_TEMPLATE.replace("{JD}", jd_ctx).replace("{CV}", cv_ctx)

    logger.info("LLM analyze call: prompt_len=%d", len(prompt))
    logger.debug("LLM analyze prompt snippet: %s", prompt[:600])

    try:
        raw = ask_llm(prompt, max_tokens=ANALYZE_MAX_TOKENS, temperature=0.15)
    except Exception as e:
        logger.exception("LLM analyze call failed")
        return None

    if isinstance(raw, str):
        raw_str = raw.strip()
        if raw_str.startswith("```") and raw_str.endswith("```"):
            raw_str = "\n".join(raw_str.splitlines()[1:-1])
        first = raw_str.find("{")
        last = raw_str.rfind("}")
        candidate = raw_str[first:last+1] if first != -1 and last != -1 and last > first else raw_str
    else:
        candidate = json.dumps(raw)

    logger.debug("LLM analyze raw candidate length: %d", len(candidate))
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            logger.info("LLM analyze returned valid JSON object")
            return parsed
        logger.error("LLM analyze returned JSON but not a dict")
    except Exception as e:
        logger.exception("ANALYZE: JSON parse failed for model output")
        return None
    return None


def _llm_call_career_suggestions(jd_text: str, cv_text: str) -> Optional[List[Dict[str, Any]]]:
    jd_ctx = _safe_trim_text(jd_text, MAX_CTX_CHARS)
    cv_ctx = _safe_trim_text(cv_text, MAX_CTX_CHARS)
    prompt = CAREER_SUGGEST_PROMPT.replace("{JD}", jd_ctx).replace("{CV}", cv_ctx)

    logger.info("LLM career-suggestion call: prompt_len=%d", len(prompt))
    logger.debug("Career-suggest prompt snippet: %s", prompt[:600])

    try:
        raw = ask_llm(prompt, max_tokens=CAREER_SUGGEST_MAX_TOKENS, temperature=0.25)
    except Exception:
        logger.exception("LLM career-suggestion call failed")
        return None

    if isinstance(raw, str):
        s = raw.strip()
        if s.startswith("```") and s.endswith("```"):
            s = "\n".join(s.splitlines()[1:-1])
        first = s.find("[")
        last = s.rfind("]")
        candidate = s[first:last+1] if first != -1 and last != -1 and last > first else s
    else:
        candidate = json.dumps(raw)

    logger.debug("Career-suggest candidate len: %d", len(candidate))
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, list):
            out = []
            for item in parsed[:3]:
                if not isinstance(item, dict):
                    continue
                out.append({
                    "title": item.get("title") or item.get("name") or "Suggestion",
                    "description": item.get("description") or item.get("plan") or "",
                    "cv_bullet": item.get("cv_bullet") or item.get("cv_bullet_point") or "",
                    "priority": item.get("priority") or "medium",
                    "resources": item.get("resources") or []
                })
            logger.info("Career-suggestion parsed %d recommendations", len(out))
            return out
        logger.error("Career-suggestion did not return a JSON list")
    except Exception:
        logger.exception("ANALYZE: career suggestions parse failed")
        return None
    return None


def _format_single_recommendation(rec: Any) -> str:
    """
    Deterministic human-readable formatting for a single recommendation entry.
    Accepts either a string or a dict with keys:
      title, description, suggestion/cv_bullet, priority, resources
    """
    if not rec:
        return ""
    if isinstance(rec, str):
        s = rec.strip()
        if not s.endswith("."):
            s = s + "."
        return s
    if isinstance(rec, dict):
        parts = []
        title = rec.get("title")
        if title:
            parts.append(f"{title}.")
        desc = rec.get("description") or ""
        if desc:
            parts.append(desc.strip().rstrip(".") + ".")
        suggestion = rec.get("suggestion") or rec.get("cv_bullet") or ""
        if suggestion:
            parts.append(f"CV bullet: {suggestion.strip().rstrip('.')}.")
        resources = rec.get("resources") or []
        if resources:
            parts.append("Resources: " + "; ".join(resources[:3]) + ".")
        return " ".join(parts)
    return str(rec)


def _build_readable_recommendations(suggestions: List[Any]) -> List[str]:
    out = []
    for s in suggestions or []:
        formatted = _format_single_recommendation(s)
        if formatted:
            out.append(formatted)
    return out


def _build_human_summary(suitability: Dict[str, Any], missing_skills: List[str], readable_recs: List[str]) -> str:
    label = suitability.get("label", "Unknown") if isinstance(suitability, dict) else str(suitability)
    score = suitability.get("score", 0.0) if isinstance(suitability, dict) else 0.0
    score_pct = int(score * 100) if isinstance(score, (float, int)) else 0
    first = f"Fit: {label} ({score_pct}%)."
    if missing_skills:
        miss_sample = ", ".join(missing_skills[:4])
        second = f"Missing skills: {miss_sample}."
    else:
        second = "No major technical skills appear missing."
    third = ""
    if readable_recs:
        third = "Top action: " + readable_recs[0]
    summary = " ".join([first, second, third]).strip()
    return summary


def _polish_with_llm(readable_list: List[str]) -> Optional[str]:
    if not readable_list:
        return None
    payload = json.dumps(readable_list, ensure_ascii=False)
    prompt = READABLE_POLISH_PROMPT.replace("{RECS}", payload)
    logger.info("LLM polish call: prompt_len=%d", len(prompt))
    try:
        out = ask_llm(prompt, max_tokens=600, temperature=0.2)
        if isinstance(out, str):
            s = out.strip()
            if s.startswith("```") and s.endswith("```"):
                s = "\n".join(s.splitlines()[1:-1])
            return s
    except Exception:
        logger.exception("ANALYZE: LLM polish failed")
        return None
    return None


def analyze_and_recommend(jd_text: str, cv_text: str) -> Dict[str, Any]:
    start = time.time()
    logger.debug("analyze_and_recommend called: jd_len=%d cv_len=%d", len(jd_text or ""), len(cv_text or ""))

    llm_result = _llm_call_analyze(jd_text, cv_text)
    if llm_result:
        def norm_list(x):
            if not x:
                return []
            return [str(i).strip().title() for i in x]

        required_skills = norm_list(llm_result.get("required_skills", []))
        cv_skills = norm_list(llm_result.get("cv_skills", []))
        missing_skills = norm_list(llm_result.get("missing_skills", []))

        # Defensive sanity
        jd_present_counts = {s: _occurrences_of_keyword_in_text(s, jd_text) for s in required_skills}
        if required_skills and all(count == 0 for count in jd_present_counts.values()):
            flags = {"jd_malformed": True, "cv_low_content": False, "possible_hallucination": True}
            timing = {"analyzed_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), "parsing_ms": 0,
                      "analysis_ms": int((time.time() - start) * 1000), "total_ms": int((time.time() - start) * 1000)}
            logger.warning("LLM analyze returned required_skills that do not appear in JD -> marking jd_malformed")
            return {
                "required_skills": [],
                "cv_skills": [],
                "missing_skills": [],
                "matched_keywords": [],
                "suitability": {"score": 0.0, "label": "Not a Fit"},
                "difficulty_estimate": {"score": 1.0, "reason": "JD non-technical or malformed (no explicit skills)"},
                "suggested_improvements": [],
                "confidence": 0.15,
                "flags": flags,
                "timing": timing,
                "readable_recommendations": [],
                "human_readable_summary": ""
            }

        mk = llm_result.get("matched_keywords", [])
        normalized_mk = []
        for item in mk or []:
            try:
                normalized_mk.append({
                    "keyword": str(item.get("keyword", "")).title(),
                    "occurrences_in_jd": int(item.get("occurrences_in_jd", 0)),
                    "occurrences_in_cv": int(item.get("occurrences_in_cv", 0)),
                    "context_jd": item.get("context_jd", [])[:2]
                })
            except Exception:
                logger.debug("Skipping malformed matched_keyword item: %s", item)
                continue

        suitability = llm_result.get("suitability", {"score": 0.0, "label": "Unknown"})
        difficulty = llm_result.get("difficulty_estimate", {"score": 0.0, "reason": ""})
        suggestions = llm_result.get("suggested_improvements", []) or []
        confidence = float(llm_result.get("confidence", 0.5))
        flags = llm_result.get("flags", {"jd_malformed": False, "cv_low_content": False, "possible_hallucination": False})

        # career suggestions (best-effort)
        career_recs = _llm_call_career_suggestions(jd_text, cv_text)
        career_entries = []
        if career_recs:
            for r in career_recs:
                career_entries.append({
                    "type": "recommendation",
                    "title": r.get("title"),
                    "description": r.get("description"),
                    "keyword": None,
                    "suggestion": r.get("cv_bullet"),
                    "priority": r.get("priority", "medium"),
                    "resources": r.get("resources", [])
                })

        combined_improvements = (suggestions or []) + career_entries

        # Build readable recommendations deterministically
        readable_recs = _build_readable_recommendations(combined_improvements)

        # Optionally polish via LLM
        polished = None
        if try_llm_for_readable:
            try:
                polished = _polish_with_llm(readable_recs)
            except Exception:
                logger.exception("Polish with LLM failed")
                polished = None

        human_summary = _build_human_summary(suitability, missing_skills, readable_recs)

        end = time.time()
        timing = {"analyzed_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), "parsing_ms": 0,
                  "analysis_ms": int((end - start) * 1000), "total_ms": int((end - start) * 1000)}

        result = {
            "required_skills": required_skills,
            "cv_skills": cv_skills,
            "missing_skills": missing_skills,
            "matched_keywords": normalized_mk,
            "suitability": suitability,
            "difficulty_estimate": difficulty,
            "suggested_improvements": combined_improvements,
            "confidence": round(min(max(confidence, 0.0), 1.0), 2),
            "flags": flags,
            "timing": timing,
            "readable_recommendations": readable_recs,
            "human_readable_summary": polished or human_summary
        }
        logger.info("analyze_and_recommend completed: required=%d missing=%d suggestions=%d duration_ms=%d",
                    len(required_skills), len(missing_skills), len(combined_improvements), timing["analysis_ms"])
        return result

    # FALLBACK hybrid
    logger.info("LLM analyze failed — using fallback hybrid pipeline")
    required = extract_skills_from_text(jd_text)
    cv_skills = extract_skills_from_text(cv_text)
    result = analyze_gap_and_keywords(required, cv_skills, jd_text, cv_text)

    jd_present_counts = {s: _occurrences_of_keyword_in_text(s, jd_text) for s in (required or [])}
    if required and all(count == 0 for count in jd_present_counts.values()):
        result["flags"] = {"jd_malformed": True, "cv_low_content": False, "possible_hallucination": False}
        result["suitability"] = {"score": 0.0, "label": "Not a Fit"}
        result["confidence"] = 0.15
        result["suggested_improvements"] = []
        result["timing"]["total_ms"] = int((time.time() - start) * 1000)
        result["readable_recommendations"] = []
        result["human_readable_summary"] = ""
        logger.warning("Fallback pipeline marked JD as malformed")
        return result

    # attach recommendations for missing skills (hybrid)
    missing = result.get("missing_skills", []) or []
    rec_entries: List[Dict[str, Any]] = []
    for skill in missing:
        try:
            rec = recommend_for_skills(skill)
            rec_entries.append({
                "type": "recommendation",
                "title": rec.get("project"),
                "description": None,
                "keyword": skill,
                "suggestion": rec.get("cv_bullet"),
                "priority": "high",
                "resources": rec.get("resources", [])
            })
        except Exception:
            logger.exception("Error while building hybrid recommendation for skill: %s", skill)
            continue

    # try career suggestion LLM in fallback mode (best-effort)
    career_recs = _llm_call_career_suggestions(jd_text, cv_text)
    if career_recs:
        for r in career_recs:
            rec_entries.append({
                "type": "recommendation",
                "title": r.get("title"),
                "description": r.get("description"),
                "keyword": None,
                "suggestion": r.get("cv_bullet"),
                "priority": r.get("priority", "medium"),
                "resources": r.get("resources", [])
            })

    existing_improvements = result.get("suggested_improvements", [])
    combined = existing_improvements + rec_entries
    result["suggested_improvements"] = combined

    # generate readable versions
    result["readable_recommendations"] = _build_readable_recommendations(combined)
    result["human_readable_summary"] = _build_human_summary(result.get("suitability", {}), result.get("missing_skills", []), result["readable_recommendations"])

    result["confidence"] = result.get("confidence", 0.6)
    result["timing"]["total_ms"] = int((time.time() - start) * 1000)
    logger.info("Fallback analyze completed: required=%d missing=%d suggestions=%d duration_ms=%d",
                len(result.get("required_skills", [])),
                len(result.get("missing_skills", [])),
                len(combined),
                result["timing"]["total_ms"])
    return result

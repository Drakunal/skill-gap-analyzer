# app/api/routes.py
import hashlib
import time
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from app.services.parser_service import parse_and_cache_bytes
from app.cache.cv_cache import get as cache_get
from app.services.analyze_service import analyze_and_recommend
from app.models.schemas import UploadCVOut, AnalyzeIn, AnalyzeOut
from app.core.logger import logger

router = APIRouter()


@router.post("/upload-cv", response_model=UploadCVOut)
def upload_cv(file: UploadFile = File(...)):
    """
    Upload CV file (pdf/docx/txt). Returns cv_id (md5 checksum), snippet and cached flag.
    """
    try:
        logger.info("Upload CV called: filename=%s, content_type=%s", file.filename, file.content_type)
        content = file.file.read()
        logger.info("Read CV bytes: %d bytes", len(content))

        cv_id, text, cached = parse_and_cache_bytes(content, file.filename)
        snippet = text[:1000]

        logger.info("CV parsed: cv_id=%s cached=%s snippet_len=%d", cv_id, cached, len(snippet))
        return UploadCVOut(cv_id=cv_id, snippet=snippet, cached=cached)
    except Exception as e:
        logger.exception("Error in upload_cv: %s", e)
        raise HTTPException(status_code=500, detail="Failed to upload and parse CV")


@router.post("/analyze", response_model=AnalyzeOut)
def analyze(payload: AnalyzeIn):
    """
    JSON-based analyze: requires job_description and cv_id in JSON body.
    """
    start = time.time()
    try:
        jd_text = payload.job_description
        logger.info("Analyze (JSON) called: cv_id=%s jd_len=%d", payload.cv_id, len(jd_text or ""))

        cv_entry = cache_get(payload.cv_id)
        if not cv_entry:
            logger.warning("Analyze (JSON): cv_id not found in cache: %s", payload.cv_id)
            raise HTTPException(status_code=404, detail="cv_id not found in cache")
        cv_text = cv_entry["text"]
        logger.debug("Analyze (JSON): cv snippet: %s", cv_text[:200])

        result = analyze_and_recommend(jd_text, cv_text)

        job_id = hashlib.md5(jd_text.encode("utf-8")).hexdigest()
        response = {
            "job_id": job_id,
            "cv_id": payload.cv_id,
            "jd_text_snippet": jd_text[:200],
            "cv_text_snippet": cv_text[:200],
            "required_skills": result.get("required_skills", []),
            "cv_skills": result.get("cv_skills", []),
            "missing_skills": result.get("missing_skills", []),
            "matched_keywords": result.get("matched_keywords", []),
            "suitability": result.get("suitability", {"score": 0.0, "label": "Unknown"}),
            "difficulty_estimate": result.get("difficulty_estimate", {"score": 0.0, "reason": ""}),
            "suggested_improvements": result.get("suggested_improvements", []),
            "confidence": result.get("confidence", 0.0),
            "flags": result.get("flags", {}),
            "timing": result.get("timing", {})
        }

        duration = time.time() - start
        logger.info("Analyze (JSON) complete: job_id=%s duration_ms=%d", job_id, int(duration * 1000))
        return JSONResponse(response)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error in analyze (JSON): %s", e)
        raise HTTPException(status_code=500, detail="Internal error during analysis")


@router.post("/analyze-form", response_model=AnalyzeOut)
def analyze_form(job_description: str = Form(...), cv_id: str = Form(...)):
    """
    Form-based analyze: accepts job_description as form data (safe for copy/paste in Swagger/UI).
    """
    start = time.time()
    try:
        jd_text = job_description
        logger.info("Analyze (form) called: cv_id=%s jd_len=%d", cv_id, len(jd_text or ""))

        cv_entry = cache_get(cv_id)
        if not cv_entry:
            logger.warning("Analyze (form): cv_id not found in cache: %s", cv_id)
            raise HTTPException(status_code=404, detail="cv_id not found in cache")
        cv_text = cv_entry["text"]
        logger.debug("Analyze (form): cv snippet: %s", cv_text[:200])

        result = analyze_and_recommend(jd_text, cv_text)

        job_id = hashlib.md5(jd_text.encode("utf-8")).hexdigest()
        response = {
            "job_id": job_id,
            "cv_id": cv_id,
            "jd_text_snippet": jd_text[:200],
            "cv_text_snippet": cv_text[:200],
            "required_skills": result.get("required_skills", []),
            "cv_skills": result.get("cv_skills", []),
            "missing_skills": result.get("missing_skills", []),
            "matched_keywords": result.get("matched_keywords", []),
            "suitability": result.get("suitability", {"score": 0.0, "label": "Unknown"}),
            "difficulty_estimate": result.get("difficulty_estimate", {"score": 0.0, "reason": ""}),
            "suggested_improvements": result.get("suggested_improvements", []),
            "confidence": result.get("confidence", 0.0),
            "flags": result.get("flags", {}),
            "timing": result.get("timing", {})
        }

        duration = time.time() - start
        logger.info("Analyze (form) complete: job_id=%s duration_ms=%d", job_id, int(duration * 1000))
        return JSONResponse(response)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error in analyze-form: %s", e)
        raise HTTPException(status_code=500, detail="Internal error during analysis")


@router.get("/health")
def health():
    logger.debug("Health check called")
    return {"status": "ok"}

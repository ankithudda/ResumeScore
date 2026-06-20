import json
import logging
from fastapi import APIRouter, Depends, Form
from backend.dependencies import valid_pdf_text
from backend.services.job_matcher import match_multiple_jobs

logger = logging.getLogger("ResumeScore.JobMatcherRouter")
router = APIRouter(prefix="/api/job-matcher", tags=["Job Matching"])

@router.post("")
async def find_best_fit_job(
    jobs_json: str = Form(...),
    resume_text: str = Depends(valid_pdf_text)
):
    try:
        job_descriptions = json.loads(jobs_json)
    except json.JSONDecodeError:
        raise ValueError("Invalid job descriptions format. Expected a JSON array.")
        
    if not isinstance(job_descriptions, list) or len(job_descriptions) == 0:
        raise ValueError("Expected a non-empty JSON array of job descriptions.")

    result = await match_multiple_jobs(resume_text, job_descriptions)
    return result
from fastapi import APIRouter, Depends, Form, Request
from backend.limiter import limiter
from backend.dependencies import valid_pdf_text
from backend.services.scorer import calculate_match_score
from backend.services.ai_analyzer import analyze_resume_with_ai

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

@router.post("/full")
@limiter.limit("5/minute")
async def full_analysis(
    request: Request,
    job_description: str = Form(...),
    resume_text: str = Depends(valid_pdf_text)
):
    tfidf_result = calculate_match_score(resume_text, job_description)
    ai_result = await analyze_resume_with_ai(resume_text, job_description)

    return {
        "tfidf_analysis": tfidf_result,
        "ai_analysis": ai_result,
        "resume_preview": resume_text[:300]
    }
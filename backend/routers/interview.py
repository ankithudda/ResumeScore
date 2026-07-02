from fastapi import APIRouter, Depends, Form, Request
from backend.limiter import limiter
from backend.dependencies import valid_pdf_text
from backend.services.interview_generator import generate_interview_questions

router = APIRouter(prefix="/api/interview-prep", tags=["Interview Preparation"])

@router.post("")
@limiter.limit("5/minute")
async def get_interview_prep(
    request: Request,
    job_description: str = Form(...),
    resume_text: str = Depends(valid_pdf_text)
):
    ai_response = await generate_interview_questions(resume_text, job_description)
    return ai_response
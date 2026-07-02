from fastapi import APIRouter, Depends, Form, Request
from backend.limiter import limiter
from backend.dependencies import valid_pdf_text
from backend.services.cover_letter_generator import generate_cover_letter_logic

router = APIRouter(prefix="/api/cover-letter", tags=["Cover Letter"])

@router.post("")
@limiter.limit("5/minute")
async def create_cover_letter(
    request: Request,
    job_description: str = Form(...),
    company_name: str = Form(...),
    resume_text: str = Depends(valid_pdf_text)
):
    
    result = await generate_cover_letter_logic(resume_text, job_description, company_name)

    return {
        "company_name": company_name,
        "cover_letter_result": result
    }
from fastapi import APIRouter, Depends, Form
from backend.dependencies import valid_pdf_text
from backend.services.roadmap_generator import generate_career_roadmap

router = APIRouter(prefix="/api/roadmap", tags=["Learning Roadmap"])

@router.post("")
async def get_learning_roadmap(
    job_description: str = Form(...),
    resume_text: str = Depends(valid_pdf_text)
):
    result = await generate_career_roadmap(resume_text, job_description)
    return result
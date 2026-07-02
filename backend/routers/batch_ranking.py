import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, Request
from backend.limiter import limiter
from backend.services.pdf_parser import extract_text_from_pdf
from backend.services.batch_ranker import rank_candidates

logger = logging.getLogger("ResumeScore.BatchRankingRouter")
router = APIRouter(prefix="/api/batch-ranking", tags=["Batch Candidate Ranking"])

MAX_RESUMES = 10

@router.post("")
@limiter.limit("3/minute")
async def batch_rank_candidates(
    request: Request,
    files: List[UploadFile] = File(...),
    job_description: str = Form(...)
):
    if len(files) == 0:
        raise ValueError("At least one resume PDF is required.")
    if len(files) > MAX_RESUMES:
        raise ValueError(f"Maximum {MAX_RESUMES} resumes per batch.")

    resumes = []
    skipped_files = []

    for file in files:
        if not file.filename.endswith(".pdf"):
            skipped_files.append(f"{file.filename} (not a PDF)")
            continue

        try:
            file_bytes = await file.read()
            resume_text = extract_text_from_pdf(file_bytes)
            if not resume_text.strip():
                skipped_files.append(f"{file.filename} (no extractable text)")
                continue
            resumes.append({"filename": file.filename, "text": resume_text})
        except Exception:
            skipped_files.append(f"{file.filename} (processing error)")
            continue

    if len(resumes) == 0:
        raise ValueError("No valid resumes could be processed.")

    result = await rank_candidates(resumes, job_description)
    result["skipped_files"] = skipped_files
    
    return result
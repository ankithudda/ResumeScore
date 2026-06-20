from fastapi import UploadFile, File, HTTPException
from backend.services.pdf_parser import extract_text_from_pdf

async def valid_pdf_text(file: UploadFile = File(...)) -> str:
    """Dependency to validate and extract text from a PDF upload."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")
    
    try:
        file_bytes = await file.read()
        text = extract_text_from_pdf(file_bytes)
        
        if not text.strip():
            raise HTTPException(status_code=422, detail="Could not extract text from PDF")
        return text
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF Processing Error: {str(e)}")

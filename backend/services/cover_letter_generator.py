import logging
from pydantic import BaseModel, Field
from backend.services.ai_client import call_and_validate

logger = logging.getLogger("ResumeScore.CoverLetterService")

# ==========================================
# 1. PYDANTIC CONTRACT SCHEMA
# ==========================================

class CoverLetterResponse(BaseModel):
    cover_letter: str = Field(..., description="Full cover letter text with \\n\\n for paragraphs")
    word_count: int = Field(default=0)

# ==========================================
# 2. DOMAIN LOGIC
# ==========================================

async def generate_cover_letter_logic(resume_text: str, job_description: str, company_name: str) -> dict:
    prompt = f"""
You are an expert career coach and professional writer.
Write a compelling, personalized cover letter based on the resume and job description below.

Requirements:
- Professional but conversational tone
- 3 paragraphs: opening, body (highlight relevant skills), closing
- Reference the company name: {company_name}
- Keep it under 300 words
- Do NOT use generic phrases like "I am writing to apply"
- IMPORTANT: You MUST escape all newlines in the cover letter text using \\n\\n. Do NOT use raw/actual line breaks inside the JSON string value.

Return ONLY a JSON object with these exact keys:
{{
    "cover_letter": "full cover letter text here with \\n\\n for paragraphs",
    "word_count": 0
}}

RESUME:
{resume_text[:2500]}

JOB DESCRIPTION:
{job_description[:1500]}

Start your response with {{
"""
    response_dict = await call_and_validate(prompt, schema=CoverLetterResponse, temperature=0.5, max_tokens=800)
    response_dict["word_count"] = len(response_dict["cover_letter"].split())
    return response_dict
import logging
from pydantic import BaseModel, Field
from typing import List
from backend.services.ai_client import call_and_validate

logger = logging.getLogger("ResumeScore.AIAnalyzer")

# ==========================================
# 1. PYDANTIC CONTRACT SCHEMA
# ==========================================

class AIAnalysisResponse(BaseModel):
    overall_feedback: str = Field(..., description="A 2-3 sentence summary of candidate fit.")
    strengths: List[str] = Field(..., description="Array of technical or structural highlights from the resume.")
    improvements: List[str] = Field(..., description="Array of missing elements or technical areas needing expansion.")
    ats_tips: List[str] = Field(..., description="Actionable ATS optimization recommendations.")
    fit_verdict: str = Field(..., description="Must be 'Strong Fit', 'Moderate Fit', or 'Weak Fit'.")

# ==========================================
# 2. DOMAIN LOGIC
# ==========================================

async def analyze_resume_with_ai(resume_text: str, job_description: str) -> dict:
    prompt = f"""
You are an expert HR recruiter and professional technical resume analyst.

Analyze this resume against the provided job description.
You MUST respond with ONLY a valid JSON object. No markdown, no code fences, no introductory explanations.

The JSON object must have exactly these keys:
{{
    "overall_feedback": "2-3 sentence summary of candidate fit",
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "improvements": ["improvement 1", "improvement 2", "improvement 3"],
    "ats_tips": ["tip 1", "tip 2"],
    "fit_verdict": "Strong Fit"
}}

The "fit_verdict" property must be exactly one of: "Strong Fit", "Moderate Fit", "Weak Fit"

RESUME:
{resume_text[:2500]}

JOB DESCRIPTION:
{job_description[:1500]}

Respond with the JSON object only. Start your response directly with {{
"""
    return await call_and_validate(prompt, schema=AIAnalysisResponse, temperature=0.2, max_tokens=1000)
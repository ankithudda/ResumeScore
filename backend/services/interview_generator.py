import logging
from pydantic import BaseModel, Field
from typing import List
from backend.services.ai_client import call_and_validate

logger = logging.getLogger("ResumeScore.InterviewGenerator")

class QuestionItem(BaseModel):
    id: int = Field(..., description="Sequential index starting from 1")
    question: str = Field(..., description="The highly specific interview question")
    type: str = Field(..., description="Must be 'Technical', 'Behavioral', or 'Resume-Specific'")
    intent: str = Field(..., description="The underlying core skill or trait the interviewer is probing")
    suggested_talking_points: str = Field(..., description="Strategic hints aligned with candidate experience")

class InterviewPrepResponse(BaseModel):
    interview_prep: List[QuestionItem]

async def generate_interview_questions(resume_text: str, job_description: str) -> dict:
    prompt = f"""
You are an expert technical interviewer and executive talent assessor.

Analyze the candidate's RESUME against the target JOB DESCRIPTION. Identify key alignment points, technology transitions, gaps, or notable projects.

Generate exactly 5-6 realistic, high-signal interview questions. Balance them between:
1. Deep Technical Questions (probing their tech stack: Python, SQL, ML metrics)
2. Behavioral Questions (probing adaptability, learning framework shifts)
3. Resume-Specific Questions (auditing their specific claimed achievements and metrics)

Requirements:
- Each question must be highly specific, never generic.
- IMPORTANT: Escape all newlines within text properties using '\\n'. Do NOT use raw/actual line breaks inside JSON string values.

Return ONLY a JSON object conforming precisely to this structural schema:
{{
  "interview_prep": [
    {{
      "id": 1,
      "question": "Specific question text here",
      "type": "Technical",
      "intent": "What you are secretly looking for when asking this",
      "suggested_talking_points": "What the candidate should emphasize from their actual experience"
    }}
  ]
}}

JOB DESCRIPTION:
{job_description[:1500]}

RESUME:
{resume_text[:2500]}

Start your response directly with the opening curly brace '{{'
"""
    return await call_and_validate(prompt, schema=InterviewPrepResponse, temperature=0.6, max_tokens=1200)
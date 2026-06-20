import logging
from pydantic import BaseModel, Field
from typing import List
from backend.services.ai_client import call_and_validate

logger = logging.getLogger("ResumeScore.RoadmapGenerator")

# ==========================================
# 1. PYDANTIC DATA SCHEMAS (The Contract)
# ==========================================

class Milestone(BaseModel):
    """Defines a specific time-bound phase in the roadmap."""
    phase: str = Field(..., description="e.g., 'Days 1-30: Foundation & Gap Closing'")
    focus_area: str = Field(..., description="The main strategic objective for this timeframe.")
    action_items: List[str] = Field(..., description="3-4 specific, actionable engineering/learning tasks.")

class ResourceItem(BaseModel):
    """Defines a recommended learning resource or tool."""
    name: str = Field(..., description="Name of the concept, course, framework, or tool.")
    reasoning: str = Field(..., description="Why this specifically builds versatile, cross-industry value.")

class CareerRoadmapResponse(BaseModel):
    """The master response structure containing the arrays of milestones and resources."""
    milestones: List[Milestone]
    resources: List[ResourceItem]

# ==========================================
# 2. BUSINESS LOGIC ENGINE
# ==========================================

async def generate_career_roadmap(resume_text: str, job_description: str) -> dict:
    """
    Formulates a specialized prompt to generate a 90-day learning roadmap,
    delegates execution to ai_client, and validates the nested schema.
    """
    
    prompt = f"""
You are an elite career strategist and technical mentor. 

Analyze the provided RESUME against the target JOB DESCRIPTION. Identify the exact skill gaps and formulate a highly actionable, 90-day learning and development roadmap. 

Strategic Directives:
- Ensure the recommended skills and project milestones highlight cross-sector adaptability. Do not lock the candidate into a single narrow industry niche; prioritize highly transferable technical, analytical, and software development skills.
- Be highly specific with technical terms (e.g., instead of "learn databases", say "master window functions in PostgreSQL").
- IMPORTANT: Escape all newlines within text properties using '\\n'. Do NOT use raw/actual line breaks inside JSON string values.

Return ONLY a JSON object conforming precisely to this structural schema:
{{
  "milestones": [
    {{
      "phase": "Days 1-30: Gap Closing",
      "focus_area": "Specific focus here...",
      "action_items": ["Action 1", "Action 2", "Action 3"]
    }}
  ],
  "resources": [
    {{
      "name": "Specific tool or skill name",
      "reasoning": "Why this builds versatile, cross-industry value"
    }}
  ]
}}

JOB DESCRIPTION:
{job_description[:1500]}

RESUME:
{resume_text[:2500]}

Start your response directly with the opening curly brace '{{'
"""
    return await call_and_validate(prompt, CareerRoadmapResponse, temperature=0.5, max_tokens=1500)
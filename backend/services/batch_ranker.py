import logging
from pydantic import BaseModel, Field
from typing import List, Dict
from backend.services.ai_client import call_and_validate
from backend.services.scorer import calculate_match_score

logger = logging.getLogger("ResumeScore.BatchRanker")

TOP_N_FOR_AI_ANALYSIS = 5

# ==========================================
# 1. PYDANTIC SCHEMAS (The Data Contract)
# ==========================================

class CandidateAnalysis(BaseModel):
    filename: str = Field(..., description="The exact resume filename being analyzed")
    strengths: List[str] = Field(..., description="2-3 key strengths for this specific role")
    concerns: List[str] = Field(..., description="1-2 gaps or concerns for this role")
    recommendation: str = Field(..., description="One-line hiring recommendation")

class TopCandidatesAIResponse(BaseModel):
    top_candidates_analysis: List[CandidateAnalysis]

# ==========================================
# 2. CASCADE RANKING ENGINE
# ==========================================

async def rank_candidates(resumes: List[Dict[str, str]], job_description: str) -> dict:
    scored = []

    for resume in resumes:
        tfidf_result = calculate_match_score(resume["text"], job_description)
        scored.append({
            "filename": resume["filename"],
            "text": resume["text"],
            "match_score": tfidf_result.get("match_score", 0.0),
            "raw_similarity": tfidf_result.get("raw_similarity", 0.0),
            "strength": tfidf_result.get("strength", "Weak")
        })

    scored.sort(key=lambda x: x["raw_similarity"], reverse=True)
    top_candidates = scored[:TOP_N_FOR_AI_ANALYSIS]

    resume_block = "\n\n".join(
        f"--- CANDIDATE: {c['filename']} ---\n{c['text'][:1000]}"
        for c in top_candidates
    )

    prompt = f"""
You are an expert technical recruiter screening candidates for a single open role.

JOB DESCRIPTION:
{job_description[:1500]}

Below are the top {len(top_candidates)} candidates, pre-ranked by an automated TF-IDF match score.
For EACH candidate, provide a hiring-focused analysis based on their resume content.

{resume_block}

IMPORTANT: Escape all newlines within text properties using '\\n'. Do NOT use raw/actual line breaks inside JSON string values.

Return ONLY a JSON object conforming precisely to this schema:
{{
    "top_candidates_analysis": [
        {{
            "filename": "exact filename as shown in the CANDIDATE header above",
            "strengths": ["Strength 1", "Strength 2", "Strength 3"],
            "concerns": ["Concern 1", "Concern 2"],
            "recommendation": "One-line hiring recommendation"
        }}
    ]
}}

Provide exactly {len(top_candidates)} entries in top_candidates_analysis — one per candidate listed above, in the same order.

Start your response directly with the opening curly brace '{{'
"""
    validated_dict = await call_and_validate(prompt, schema=TopCandidatesAIResponse, temperature=0.4, max_tokens=2500)

    public_rankings = [
        {
            "filename": c["filename"],
            "match_score": c["match_score"],
            "raw_similarity": c["raw_similarity"],
            "strength": c["strength"],
        }
        for c in scored
    ]

    return {
        "rankings": public_rankings,
        "top_candidates_analysis": validated_dict["top_candidates_analysis"]
    }
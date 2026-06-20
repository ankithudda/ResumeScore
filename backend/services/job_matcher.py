import logging
from pydantic import BaseModel, Field
from typing import List, Dict
from backend.services.ai_client import call_and_validate
from backend.services.scorer import calculate_match_score

logger = logging.getLogger("ResumeScore.JobMatcher")

# ==========================================
# 1. PYDANTIC SCHEMAS (The Data Contract)
# ==========================================

class BestMatchAnalysis(BaseModel):
    label: str = Field(..., description="The identifier for the winning job description")
    why_best_fit: str = Field(..., description="Executive summary of why this is the optimal path")
    key_strengths_for_this_role: List[str] = Field(..., description="Core technical alignments")
    watch_out_for: List[str] = Field(..., description="Potential skill gaps or risks")

# ==========================================
# 2. CASCADE RANKING ENGINE
# ==========================================

async def match_multiple_jobs(resume_text: str, job_descriptions: List[Dict[str, str]]) -> dict:
    rankings = []   
    for jd in job_descriptions:
        label = jd["label"]
        text = jd["text"]
        
        tfidf_result = calculate_match_score(resume_text, text) 
        score = tfidf_result.get("match_score", 0.0)
        raw_similarity = tfidf_result.get("raw_similarity", 0.0)

        rankings.append({
            "label": label,
            "match_score": score,
            "raw_similarity": raw_similarity
        })
        
    rankings.sort(key=lambda x: x["raw_similarity"], reverse=True)
    
    top_job_label = rankings[0]["label"]  
    top_job_text = next(jd["text"] for jd in job_descriptions if jd["label"] == top_job_label)
    
    prompt = f"""
You are an expert technical career strategist.
The candidate's resume has mathematically matched highest with the following job description: '{top_job_label}'.

Analyze the alignment. Provide a structured analysis detailing why it's the best fit, 
the exact technical strengths they bring, and potential gaps they need to watch out for.

Return ONLY a JSON object matching this schema:
{{
    "label": "{top_job_label}",
    "why_best_fit": "Clear, concise reason...",
    "key_strengths_for_this_role": ["Strength 1", "Strength 2"],
    "watch_out_for": ["Gap 1", "Gap 2"]
}}

RESUME:
{resume_text[:2000]}

TOP JOB DESCRIPTION ({top_job_label}):
{top_job_text[:1500]}

Start with {{
"""
    validated_dict = await call_and_validate(prompt, schema=BestMatchAnalysis, temperature=0.5, max_tokens=1500)
    
    return {
        "rankings": rankings,
        "best_match_analysis": validated_dict
    }
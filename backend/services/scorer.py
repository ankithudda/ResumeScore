import logging
from pydantic import BaseModel, Field
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("ResumeScore.Scorer")

# ==========================================
# 1. PYDANTIC CONTRACT SCHEMA
# ==========================================
class TFIDFScoreResponse(BaseModel):
    """Enforces strict structure for the deterministic TF-IDF scoring engine."""
    match_score: float = Field(default=0.0, description="Cosine similarity scaled to 100, boosted x3.5 and capped at 98.5 for display")
    raw_similarity: float = Field(default=0.0, description="Unboosted cosine similarity (0-100), used for ranking/sorting")
    missing_keywords: List[str] = Field(default_factory=list, description="Top missing n-grams")
    strength: str = Field(default="Error", description="Categorical fit representation")

# ==========================================
# 2. DOMAIN LOGIC
# ==========================================
def calculate_match_score(resume_text: str, job_description: str) -> dict:
    """
    Calculates the cosine similarity between the resume and JD.

    Returns both:
      - match_score: boosted (x3.5) and capped at 98.5 — a friendlier number
        for the single-resume gauge in the UI.
      - raw_similarity: the unboosted 0-100 cosine similarity — use this for
        sorting/ranking multiple candidates or job descriptions, since
        match_score saturates above ~28% raw similarity and loses relative
        ordering at exactly the range where it matters most.
    """
    try:
        if not resume_text.strip() or not job_description.strip():
            logger.warning("Empty text passed to scorer. Bypassing matrix calculation.")
            return TFIDFScoreResponse(match_score=0.0, raw_similarity=0.0, missing_keywords=[], strength="Weak").model_dump()

        documents = [resume_text, job_description]

        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2)
        )

        tfidf_matrix = vectorizer.fit_transform(documents)

        similarity_score = cosine_similarity(
            tfidf_matrix[0:1],
            tfidf_matrix[1:2]
        )[0][0]

        raw_percentage = float(similarity_score) * 100
        boosted_score = raw_percentage * 3.5
        match_percentage = min(98.5, round(boosted_score, 1))

        feature_names = vectorizer.get_feature_names_out()
        jd_vector = tfidf_matrix[1].toarray()[0]
        resume_vector = tfidf_matrix[0].toarray()[0]

        missing_indices = [
            i for i in range(len(feature_names))
            if jd_vector[i] > 0 and resume_vector[i] == 0
        ]

        missing_indices = sorted(missing_indices, key=lambda idx: jd_vector[idx], reverse=True)
        missing_keywords = [feature_names[i] for i in missing_indices[:10]]

        strength = (
            "Strong" if match_percentage >= 70 else
            "Moderate" if match_percentage >= 40 else
            "Weak"
        )

        result = TFIDFScoreResponse(
            match_score=match_percentage,
            raw_similarity=round(raw_percentage, 4),
            missing_keywords=missing_keywords,
            strength=strength
        )
        return result.model_dump()

    except ValueError as ve:
        logger.warning(f"TF-IDF Vectorizer warning: {str(ve)}")
        raise ValueError(f"Text processing error: {str(ve)}")

    except Exception as e:
        logger.error(f"TF-IDF Scoring Engine failed unexpectedly: {str(e)}")
        raise RuntimeError("TF-IDF Scoring Engine failed unexpectedly.")
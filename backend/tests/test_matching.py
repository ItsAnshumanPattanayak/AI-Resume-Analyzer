from app.similarity import (
    calculate_combined_similarity,
    calculate_tfidf_similarity,
)
from app.skills import (
    compare_resume_and_job_skills,
)


def test_tfidf_similarity_returns_percentage(
    sample_resume_text: str,
    sample_job_description: str,
) -> None:
    score = calculate_tfidf_similarity(
        resume_text=sample_resume_text,
        job_description=sample_job_description,
    )

    assert isinstance(score, float)
    assert 0 <= score <= 100


def test_similar_documents_score_above_zero() -> None:
    resume = (
        "Python developer experienced with FastAPI "
        "SQL and machine learning."
    )

    job = (
        "Hiring a Python developer with FastAPI "
        "and machine learning experience."
    )

    score = calculate_tfidf_similarity(
        resume,
        job,
    )

    assert score > 0


def test_empty_document_similarity() -> None:
    score = calculate_tfidf_similarity(
        "",
        "Python developer required",
    )

    assert score == 0.0


def test_combined_similarity() -> None:
    result = calculate_combined_similarity(
        tfidf_similarity=40.0,
        semantic_similarity=80.0,
    )

    assert result["combined_percentage"] == 66.0
    assert result["tfidf_percentage"] == 40.0
    assert result["semantic_percentage"] == 80.0


def test_skill_comparison(
    sample_resume_text: str,
    sample_job_description: str,
) -> None:
    result = compare_resume_and_job_skills(
        resume_text=sample_resume_text,
        job_description=sample_job_description,
    )

    assert "python" in result["matched_skills"]
    assert result["matched_count"] > 0
    assert 0 <= result[
        "skill_match_percentage"
    ] <= 100
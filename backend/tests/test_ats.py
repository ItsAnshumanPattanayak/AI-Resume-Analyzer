from app.ats import (
    calculate_ats_score,
    calculate_contact_score,
    calculate_resume_length_score,
    detect_quantified_achievements,
)
from app.extractor import (
    extract_resume_information,
)
from app.skills import (
    compare_resume_and_job_skills,
)


def test_contact_score(
    sample_resume_text: str,
) -> None:
    parsed_data = extract_resume_information(
        sample_resume_text
    )

    score = calculate_contact_score(
        parsed_data
    )

    assert score == 100.0


def test_resume_length_score_is_valid() -> None:
    text = "Python " * 400

    score = calculate_resume_length_score(
        text
    )

    assert score == 100.0


def test_detect_quantified_achievements() -> None:
    text = """
    Improved model accuracy by 18%.
    Processed 10,000 customer records.
    Developed a FastAPI application.
    """

    results = detect_quantified_achievements(
        text
    )

    assert len(results) >= 2


def test_complete_ats_score(
    sample_resume_text: str,
    sample_job_description: str,
) -> None:
    parsed_data = extract_resume_information(
        sample_resume_text
    )

    skill_comparison = (
        compare_resume_and_job_skills(
            sample_resume_text,
            sample_job_description,
        )
    )

    result = calculate_ats_score(
        resume_text=sample_resume_text,
        parsed_data=parsed_data,
        skill_comparison=skill_comparison,
        content_similarity=70.0,
    )

    assert 0 <= result["overall_score"] <= 100
    assert result["rating"] in {
        "Excellent match",
        "Good match",
        "Moderate match",
        "Low match",
        "Very low match",
    }

    assert "recommendations" in result
    assert "component_scores" in result
from app.advisor import (
    analyze_resume_quality,
    detect_metrics,
    detect_weak_phrases,
)
from app.extractor import (
    extract_resume_information,
)
from app.skills import (
    compare_resume_and_job_skills,
)


def test_detect_weak_phrases() -> None:
    text = """
    Worked on an AI project.
    Used Python and FastAPI.
    Responsible for testing.
    """

    results = detect_weak_phrases(text)

    detected = {
        item["weak_phrase"]
        for item in results
    }

    assert "worked on" in detected
    assert "used" in detected
    assert "responsible for" in detected


def test_detect_metrics() -> None:
    text = """
    Improved model accuracy by 18%.
    Processed 5,000 records.
    """

    results = detect_metrics(text)

    assert len(results) == 2


def test_complete_quality_analysis(
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

    result = analyze_resume_quality(
        resume_text=sample_resume_text,
        parsed_data=parsed_data,
        skill_comparison=skill_comparison,
    )

    assert 0 <= result["quality_score"] <= 100

    assert result["quality_rating"] in {
        "Excellent",
        "Good",
        "Needs improvement",
        "Weak",
    }

    assert "priority_recommendations" in result
    assert "bullet_point_templates" in result
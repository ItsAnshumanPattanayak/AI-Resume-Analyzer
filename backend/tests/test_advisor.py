from app.advisor import (
    analyze_resume_quality,
    redact_evidence,
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


def test_advanced_feedback_is_deterministic_and_redacts_evidence() -> None:
    resume_text = """
    Sample Candidate
    sample@example.com | +1 555 123 4567 | https://example.com/profile
    SUMMARY
    I am a hardworking quick learner with excellent skills.
    SKILLS
    Python, Python, SQL, Docker
    PROJECTS
    - Worked on an API and improved processing speed.
    - Worked on an API and improved processing speed.
    - I helped with various tasks.
    EDUCATION
    B.Tech Computer Science
    """
    parsed_data = extract_resume_information(resume_text)

    first = analyze_resume_quality(resume_text, parsed_data)
    second = analyze_resume_quality(resume_text, parsed_data)

    assert first == second
    assert first["priority_actions"] == sorted(
        first["priority_actions"],
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}[item["priority"]],
            item["category"],
            item["id"],
        ),
    )
    evidence = " ".join(
        bullet["evidence"]
        for bullet in first["bullet_feedback"]
    )
    assert "sample@example.com" not in evidence
    assert "+1 555" not in evidence
    assert "https://" not in evidence
    assert first["quantification_opportunities"]
    assert first["content_issues"]
    assert first["repetition_issues"]
    assert first["contact_information_feedback"]["strengths"]


def test_projects_substitute_for_experience_for_fresher() -> None:
    resume_text = """
    SUMMARY
    Computer science student building Python applications.
    SKILLS
    Python, FastAPI, SQL
    PROJECTS
    - Built a REST API using FastAPI and SQL for coursework.
    EDUCATION
    Bachelor of Technology in Computer Science
    """
    result = analyze_resume_quality(
        resume_text,
        extract_resume_information(resume_text),
    )
    experience = next(
        item for item in result["section_feedback"]
        if item["section_name"] == "experience"
    )

    assert experience["detected"] is False
    assert experience["issues"] == []
    assert "Projects can demonstrate" in experience["suggestions"][0]


def test_redact_evidence_removes_contact_data() -> None:
    value = "Reach me at person@example.com, +91 98765 43210, https://example.com and 42 Main Street."
    result = redact_evidence(value)

    assert "person@example.com" not in result
    assert "98765" not in result
    assert "example.com" not in result
    assert "42 Main Street" not in result

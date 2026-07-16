from app.extractor import (
    extract_email,
    extract_name,
    extract_phone,
    extract_resume_information,
    extract_skills,
    extract_urls,
)


def test_extract_email() -> None:
    text = "Contact me at anshuman@example.com"

    assert extract_email(text) == (
        "anshuman@example.com"
    )


def test_extract_indian_phone() -> None:
    text = "Phone: +91 9876543210"

    result = extract_phone(text)

    assert result is not None
    assert "9876543210" in result


def test_extract_urls() -> None:
    text = """
    LinkedIn: https://linkedin.com/in/anshuman
    GitHub: https://github.com/anshuman
    """

    urls = extract_urls(text)

    assert len(urls) == 2
    assert any(
        "linkedin.com" in url
        for url in urls
    )
    assert any(
        "github.com" in url
        for url in urls
    )


def test_extract_name(
    sample_resume_text: str,
) -> None:
    result = extract_name(
        sample_resume_text
    )

    assert result == "Anshuman Pattanayak"


def test_extract_skills(
    sample_resume_text: str,
) -> None:
    result = extract_skills(
        sample_resume_text
    )

    all_detected = {
        skill
        for skills in result.values()
        for skill in skills
    }

    assert "python" in all_detected
    assert "machine learning" in all_detected
    assert "fastapi" in all_detected


def test_complete_information_extraction(
    sample_resume_text: str,
) -> None:
    result = extract_resume_information(
        sample_resume_text
    )

    assert result["name"] == "Anshuman Pattanayak"
    assert result["email"] == "anshuman@example.com"
    assert result["phone"] is not None
    assert result["links"]["github"] is not None
    assert result["skills"]["total_detected"] > 0
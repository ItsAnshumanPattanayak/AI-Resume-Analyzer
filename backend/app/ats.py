import re
from typing import Any


ATS_WEIGHTS = {
    "skills_match": 40,
    "text_similarity": 25,
    "resume_sections": 15,
    "contact_information": 10,
    "resume_length": 10,
}


EXPECTED_SECTIONS = {
    "summary",
    "skills",
    "experience",
    "education",
    "projects",
}


def calculate_contact_score(parsed_data: dict[str, Any]) -> float:
    """
    Score the availability of contact and professional links.
    Maximum raw score: 100.
    """

    score = 0

    if parsed_data.get("email"):
        score += 35

    if parsed_data.get("phone"):
        score += 30

    links = parsed_data.get("links", {})

    if links.get("linkedin"):
        score += 20

    if links.get("github"):
        score += 15

    return min(float(score), 100.0)


def calculate_section_score(parsed_data: dict[str, Any]) -> float:
    """
    Score recognized resume sections.
    """

    sections = parsed_data.get("sections", {})

    detected_sections = {
        section.lower()
        for section in sections
        if sections.get(section)
    }

    matched_sections = EXPECTED_SECTIONS.intersection(
        detected_sections
    )

    section_score = (
        len(matched_sections) / len(EXPECTED_SECTIONS)
    ) * 100

    return round(section_score, 2)


def calculate_resume_length_score(resume_text: str) -> float:
    """
    Give a basic score according to resume word count.

    This is only a heuristic and not an official ATS rule.
    """

    word_count = len(resume_text.split())

    if 300 <= word_count <= 900:
        return 100.0

    if 200 <= word_count < 300:
        return 80.0

    if 900 < word_count <= 1200:
        return 80.0

    if 120 <= word_count < 200:
        return 60.0

    if 1200 < word_count <= 1500:
        return 60.0

    if 60 <= word_count < 120:
        return 35.0

    if word_count > 1500:
        return 35.0

    return 10.0


def detect_quantified_achievements(resume_text: str) -> list[str]:
    """
    Detect lines containing measurable achievements.

    Examples:
    - Improved accuracy by 18%
    - Processed 10,000 records
    - Built 15 projects
    """

    patterns = [
        r"\b\d+(?:\.\d+)?\s?%",
        r"\b\d{1,3}(?:,\d{3})+\b",
        r"\b(?:increased|improved|reduced|decreased|saved|grew)"
        r".{0,40}\d+",
    ]

    achievement_lines = []

    for line in resume_text.splitlines():
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        if any(
            re.search(pattern, cleaned_line, flags=re.IGNORECASE)
            for pattern in patterns
        ):
            achievement_lines.append(cleaned_line)

    return achievement_lines


def build_recommendations(
    parsed_data: dict[str, Any],
    skill_comparison: dict[str, Any],
    text_similarity: float,
    resume_text: str,
) -> list[str]:
    """
    Generate rule-based resume improvement suggestions.
    """

    recommendations = []

    if not parsed_data.get("email"):
        recommendations.append(
            "Add a professional email address."
        )

    if not parsed_data.get("phone"):
        recommendations.append(
            "Add a valid phone number."
        )

    links = parsed_data.get("links", {})

    if not links.get("linkedin"):
        recommendations.append(
            "Add your LinkedIn profile link."
        )

    if not links.get("github"):
        recommendations.append(
            "Add your GitHub profile, especially for technical roles."
        )

    sections = parsed_data.get("sections", {})

    missing_sections = sorted(
        EXPECTED_SECTIONS.difference(sections.keys())
    )

    if missing_sections:
        recommendations.append(
            "Add or clearly label these resume sections: "
            + ", ".join(missing_sections)
            + "."
        )

    missing_skills = skill_comparison.get("missing_skills", [])

    if missing_skills:
        recommendations.append(
            "The job description mentions skills not detected in your "
            "resume: "
            + ", ".join(missing_skills[:10])
            + ". Add only the skills you genuinely possess."
        )

    if text_similarity < 30:
        recommendations.append(
            "Your resume has low keyword alignment with the job "
            "description. Tailor your summary, skills and project "
            "descriptions to the role."
        )

    quantified_achievements = detect_quantified_achievements(
        resume_text
    )

    if not quantified_achievements:
        recommendations.append(
            "Add measurable results to projects or experience, such "
            "as accuracy improvement, users served, records processed "
            "or time saved."
        )

    if len(resume_text.split()) < 200:
        recommendations.append(
            "The resume appears short. Add relevant project impact, "
            "technical details and achievements."
        )

    return recommendations


def calculate_ats_score(
    resume_text: str,
    parsed_data: dict[str, Any],
    skill_comparison: dict[str, Any],
    text_similarity: float,
) -> dict:
    """
    Calculate a transparent, rule-based ATS compatibility score.
    """

    skill_match_score = skill_comparison.get(
        "skill_match_percentage",
        0.0,
    )

    contact_score = calculate_contact_score(parsed_data)
    section_score = calculate_section_score(parsed_data)
    resume_length_score = calculate_resume_length_score(
        resume_text
    )

    weighted_scores = {
        "skills_match": (
            skill_match_score
            * ATS_WEIGHTS["skills_match"]
            / 100
        ),
        "text_similarity": (
            text_similarity
            * ATS_WEIGHTS["text_similarity"]
            / 100
        ),
        "resume_sections": (
            section_score
            * ATS_WEIGHTS["resume_sections"]
            / 100
        ),
        "contact_information": (
            contact_score
            * ATS_WEIGHTS["contact_information"]
            / 100
        ),
        "resume_length": (
            resume_length_score
            * ATS_WEIGHTS["resume_length"]
            / 100
        ),
    }

    total_score = sum(weighted_scores.values())
    total_score = round(min(total_score, 100.0), 2)

    if total_score >= 80:
        rating = "Excellent match"
    elif total_score >= 65:
        rating = "Good match"
    elif total_score >= 50:
        rating = "Moderate match"
    elif total_score >= 35:
        rating = "Low match"
    else:
        rating = "Very low match"

    return {
        "overall_score": total_score,
        "rating": rating,
        "weights": ATS_WEIGHTS,
        "component_scores": {
            "skills_match": round(skill_match_score, 2),
            "text_similarity": round(text_similarity, 2),
            "resume_sections": round(section_score, 2),
            "contact_information": round(contact_score, 2),
            "resume_length": round(resume_length_score, 2),
        },
        "weighted_contribution": {
            key: round(value, 2)
            for key, value in weighted_scores.items()
        },
        "quantified_achievements": detect_quantified_achievements(
            resume_text
        ),
        "recommendations": build_recommendations(
            parsed_data=parsed_data,
            skill_comparison=skill_comparison,
            text_similarity=text_similarity,
            resume_text=resume_text,
        ),
        "disclaimer": (
            "This is a custom compatibility score, not the score of "
            "a specific commercial applicant tracking system."
        ),
    }
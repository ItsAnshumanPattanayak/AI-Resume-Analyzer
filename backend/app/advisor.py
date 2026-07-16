import re
from collections import Counter
from typing import Any


STRONG_ACTION_VERBS = {
    "achieved",
    "analyzed",
    "automated",
    "built",
    "collaborated",
    "created",
    "decreased",
    "delivered",
    "designed",
    "developed",
    "engineered",
    "enhanced",
    "evaluated",
    "implemented",
    "improved",
    "increased",
    "integrated",
    "launched",
    "led",
    "maintained",
    "managed",
    "optimized",
    "processed",
    "reduced",
    "researched",
    "resolved",
    "scaled",
    "tested",
    "trained",
    "visualized",
}

WEAK_PHRASES = {
    "worked on": "developed",
    "responsible for": "managed",
    "helped with": "contributed to",
    "participated in": "collaborated on",
    "did": "completed",
    "made": "created",
    "used": "applied",
    "learned about": "gained practical experience with",
    "knowledge of": "experience with",
    "familiar with": "worked with",
}

EXPECTED_SECTIONS = {
    "summary",
    "skills",
    "experience",
    "education",
    "projects",
}

SUMMARY_HEADINGS = {
    "summary",
    "professional summary",
    "career summary",
    "profile",
    "objective",
    "career objective",
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "using",
    "was",
    "were",
    "with",
}


def get_nonempty_lines(text: str) -> list[str]:
    """
    Return cleaned, non-empty resume lines.
    """

    return [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
        if line.strip()
    ]


def is_probable_heading(line: str) -> bool:
    """
    Estimate whether a line is a resume section heading.
    """

    cleaned_line = re.sub(
        r"[^A-Za-z ]",
        "",
        line,
    ).strip()

    if not cleaned_line:
        return False

    words = cleaned_line.split()

    if len(words) > 5:
        return False

    return (
        line.isupper()
        or cleaned_line.lower()
        in {
            "summary",
            "skills",
            "experience",
            "education",
            "projects",
            "certifications",
            "achievements",
            "internships",
        }
    )


def detect_weak_phrases(
    resume_text: str,
) -> list[dict[str, str]]:
    """
    Find weak or vague phrases and suggest stronger alternatives.
    """

    findings = []
    lowercase_text = resume_text.lower()

    for weak_phrase, replacement in WEAK_PHRASES.items():
        if weak_phrase in lowercase_text:
            findings.append(
                {
                    "weak_phrase": weak_phrase,
                    "suggested_replacement": replacement,
                }
            )

    return findings


def detect_action_verb_usage(
    resume_text: str,
) -> dict[str, Any]:
    """
    Analyze whether project and experience lines begin with
    strong action verbs.
    """

    lines = get_nonempty_lines(resume_text)

    candidate_lines = []
    strong_lines = []
    weak_lines = []

    for line in lines:
        if is_probable_heading(line):
            continue

        word_count = len(line.split())

        if word_count < 5:
            continue

        candidate_lines.append(line)

        first_word_match = re.match(
            r"^[^A-Za-z]*([A-Za-z]+)",
            line,
        )

        if not first_word_match:
            weak_lines.append(line)
            continue

        first_word = first_word_match.group(1).lower()

        if first_word in STRONG_ACTION_VERBS:
            strong_lines.append(line)
        else:
            weak_lines.append(line)

    if candidate_lines:
        action_verb_percentage = (
            len(strong_lines)
            / len(candidate_lines)
        ) * 100
    else:
        action_verb_percentage = 0.0

    return {
        "candidate_lines_checked": len(candidate_lines),
        "strong_action_lines": strong_lines,
        "weak_opening_lines": weak_lines[:15],
        "action_verb_percentage": round(
            action_verb_percentage,
            2,
        ),
    }


def detect_metrics(
    resume_text: str,
) -> list[str]:
    """
    Detect resume lines containing measurable evidence.
    """

    metric_patterns = [
        r"\b\d+(?:\.\d+)?\s?%",
        r"\b\d{1,3}(?:,\d{3})+\b",
        r"\b\d+\s*(?:users?|records?|projects?|models?|files?)\b",
        r"\b\d+\s*(?:hours?|days?|weeks?|months?)\b",
        r"\b\d+(?:\.\d+)?\s*(?:ms|seconds?|minutes?)\b",
        r"\b(?:increased|improved|reduced|saved|decreased)"
        r".{0,50}\d+",
    ]

    metric_lines = []

    for line in get_nonempty_lines(resume_text):
        if any(
            re.search(
                pattern,
                line,
                flags=re.IGNORECASE,
            )
            for pattern in metric_patterns
        ):
            if line not in metric_lines:
                metric_lines.append(line)

    return metric_lines


def detect_short_content_lines(
    resume_text: str,
) -> list[str]:
    """
    Detect lines that may be too vague to communicate impact.
    """

    short_lines = []

    for line in get_nonempty_lines(resume_text):
        if is_probable_heading(line):
            continue

        word_count = len(line.split())

        if 3 <= word_count <= 7:
            if not re.search(
                r"@|https?://|\+?\d{10,}",
                line,
            ):
                short_lines.append(line)

    return short_lines[:15]


def detect_repeated_words(
    resume_text: str,
    minimum_count: int = 5,
) -> list[dict[str, Any]]:
    """
    Identify frequently repeated meaningful words.
    """

    words = re.findall(
        r"\b[a-zA-Z][a-zA-Z+#.-]{2,}\b",
        resume_text.lower(),
    )

    filtered_words = [
        word
        for word in words
        if word not in STOP_WORDS
    ]

    word_counts = Counter(filtered_words)

    repeated_words = [
        {
            "word": word,
            "count": count,
        }
        for word, count in word_counts.most_common()
        if count >= minimum_count
    ]

    return repeated_words[:15]


def evaluate_summary(
    parsed_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate the extracted summary section.
    """

    sections = parsed_data.get("sections", {})
    summary = sections.get("summary", "").strip()

    if not summary:
        return {
            "present": False,
            "word_count": 0,
            "score": 0,
            "feedback": [
                "Add a short professional summary tailored to the target role."
            ],
        }

    word_count = len(summary.split())
    feedback = []
    score = 100

    if word_count < 25:
        score -= 35
        feedback.append(
            "The summary is too short. Mention your role, strongest "
            "skills, project experience and career direction."
        )

    if word_count > 100:
        score -= 25
        feedback.append(
            "The summary is lengthy. Keep it focused and under "
            "approximately 100 words."
        )

    lowercase_summary = summary.lower()

    if not any(
        skill in lowercase_summary
        for skill in [
            "python",
            "machine learning",
            "data analysis",
            "backend",
            "artificial intelligence",
            "software",
            "developer",
            "engineer",
        ]
    ):
        score -= 20
        feedback.append(
            "Mention your main technical area or target role."
        )

    if not re.search(
        r"\b(?:built|developed|created|implemented|designed)\b",
        lowercase_summary,
    ):
        score -= 15
        feedback.append(
            "Mention practical work such as projects, internships "
            "or applications you developed."
        )

    return {
        "present": True,
        "word_count": word_count,
        "score": max(score, 0),
        "feedback": feedback,
        "text": summary,
    }


def evaluate_sections(
    parsed_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Detect missing expected resume sections.
    """

    sections = parsed_data.get("sections", {})

    detected_sections = {
        section.lower()
        for section, content in sections.items()
        if content
    }

    missing_sections = sorted(
        EXPECTED_SECTIONS.difference(
            detected_sections
        )
    )

    return {
        "detected_sections": sorted(
            detected_sections
        ),
        "missing_sections": missing_sections,
        "section_completion_percentage": round(
            (
                len(
                    EXPECTED_SECTIONS.intersection(
                        detected_sections
                    )
                )
                / len(EXPECTED_SECTIONS)
            )
            * 100,
            2,
        ),
    }


def generate_bullet_template(
    missing_skills: list[str],
) -> list[str]:
    """
    Generate safe templates rather than inventing achievements.

    Users must replace placeholders with truthful information.
    """

    suggestions = [
        (
            "Developed [project or feature] using [technology], "
            "resulting in [measurable outcome]."
        ),
        (
            "Implemented [technical solution] to solve [problem], "
            "improving [metric] by [X%]."
        ),
        (
            "Built and tested [application/model/API] using "
            "[tools], processing [number] records or users."
        ),
        (
            "Collaborated with [team size] members to deliver "
            "[project] within [time period]."
        ),
    ]

    if missing_skills:
        suggestions.append(
            "Applied [relevant skill you genuinely possess] in "
            "[project or internship] to achieve [specific result]."
        )

    return suggestions


def calculate_quality_score(
    summary_result: dict[str, Any],
    section_result: dict[str, Any],
    action_result: dict[str, Any],
    metric_lines: list[str],
    weak_phrases: list[dict[str, str]],
) -> float:
    """
    Calculate an explainable resume-writing quality score.
    """

    summary_score = summary_result.get(
        "score",
        0,
    )

    section_score = section_result.get(
        "section_completion_percentage",
        0,
    )

    action_score = action_result.get(
        "action_verb_percentage",
        0,
    )

    metrics_score = min(
        len(metric_lines) * 20,
        100,
    )

    weak_phrase_score = max(
        100 - len(weak_phrases) * 15,
        0,
    )

    quality_score = (
        summary_score * 0.20
        + section_score * 0.25
        + action_score * 0.20
        + metrics_score * 0.20
        + weak_phrase_score * 0.15
    )

    return round(
        max(0.0, min(quality_score, 100.0)),
        2,
    )


def build_priority_recommendations(
    summary_result: dict[str, Any],
    section_result: dict[str, Any],
    action_result: dict[str, Any],
    metric_lines: list[str],
    weak_phrases: list[dict[str, str]],
    missing_skills: list[str],
    short_lines: list[str],
) -> list[dict[str, str]]:
    """
    Build prioritized and explainable recommendations.
    """

    recommendations = []

    if not summary_result.get("present"):
        recommendations.append(
            {
                "priority": "high",
                "category": "summary",
                "recommendation": (
                    "Add a professional summary that mentions your "
                    "target role, strongest skills and practical projects."
                ),
            }
        )
    else:
        for feedback in summary_result.get(
            "feedback",
            [],
        ):
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "summary",
                    "recommendation": feedback,
                }
            )

    missing_sections = section_result.get(
        "missing_sections",
        [],
    )

    if missing_sections:
        recommendations.append(
            {
                "priority": "high",
                "category": "structure",
                "recommendation": (
                    "Add or clearly label these sections: "
                    + ", ".join(missing_sections)
                    + "."
                ),
            }
        )

    if action_result.get(
        "action_verb_percentage",
        0,
    ) < 50:
        recommendations.append(
            {
                "priority": "high",
                "category": "wording",
                "recommendation": (
                    "Begin more project and experience bullets with "
                    "strong action verbs such as Developed, Built, "
                    "Implemented, Optimized or Automated."
                ),
            }
        )

    if not metric_lines:
        recommendations.append(
            {
                "priority": "high",
                "category": "impact",
                "recommendation": (
                    "Add measurable outcomes. Include truthful values "
                    "such as model accuracy, records processed, time "
                    "saved, users supported or performance improvement."
                ),
            }
        )

    if weak_phrases:
        replacements = ", ".join(
            (
                f"'{item['weak_phrase']}' → "
                f"'{item['suggested_replacement']}'"
            )
            for item in weak_phrases[:5]
        )

        recommendations.append(
            {
                "priority": "medium",
                "category": "wording",
                "recommendation": (
                    "Replace weak phrases with stronger wording: "
                    + replacements
                    + "."
                ),
            }
        )

    if missing_skills:
        recommendations.append(
            {
                "priority": "medium",
                "category": "job alignment",
                "recommendation": (
                    "The job description includes skills not detected "
                    "in the resume: "
                    + ", ".join(missing_skills[:10])
                    + ". Add them only when you genuinely have relevant "
                    "experience."
                ),
            }
        )

    if short_lines:
        recommendations.append(
            {
                "priority": "medium",
                "category": "detail",
                "recommendation": (
                    "Expand vague project or experience lines by adding "
                    "the problem, technology, contribution and outcome."
                ),
            }
        )

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    return sorted(
        recommendations,
        key=lambda item: priority_order.get(
            item["priority"],
            3,
        ),
    )


def analyze_resume_quality(
    resume_text: str,
    parsed_data: dict[str, Any],
    skill_comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run the complete resume-improvement analysis.
    """

    if not resume_text.strip():
        raise ValueError(
            "Resume text is required for quality analysis."
        )

    if skill_comparison is None:
        skill_comparison = {}

    weak_phrases = detect_weak_phrases(
        resume_text
    )

    action_result = detect_action_verb_usage(
        resume_text
    )

    metric_lines = detect_metrics(
        resume_text
    )

    short_lines = detect_short_content_lines(
        resume_text
    )

    repeated_words = detect_repeated_words(
        resume_text
    )

    summary_result = evaluate_summary(
        parsed_data
    )

    section_result = evaluate_sections(
        parsed_data
    )

    missing_skills = skill_comparison.get(
        "missing_skills",
        [],
    )

    quality_score = calculate_quality_score(
        summary_result=summary_result,
        section_result=section_result,
        action_result=action_result,
        metric_lines=metric_lines,
        weak_phrases=weak_phrases,
    )

    if quality_score >= 80:
        quality_rating = "Excellent"
    elif quality_score >= 65:
        quality_rating = "Good"
    elif quality_score >= 50:
        quality_rating = "Needs improvement"
    else:
        quality_rating = "Weak"

    recommendations = build_priority_recommendations(
        summary_result=summary_result,
        section_result=section_result,
        action_result=action_result,
        metric_lines=metric_lines,
        weak_phrases=weak_phrases,
        missing_skills=missing_skills,
        short_lines=short_lines,
    )

    return {
        "quality_score": quality_score,
        "quality_rating": quality_rating,
        "summary_analysis": summary_result,
        "section_analysis": section_result,
        "action_verb_analysis": action_result,
        "quantified_achievement_lines": metric_lines,
        "weak_phrases": weak_phrases,
        "possible_vague_lines": short_lines,
        "repeated_words": repeated_words,
        "priority_recommendations": recommendations,
        "bullet_point_templates": generate_bullet_template(
            missing_skills
        ),
        "disclaimer": (
            "Generated templates contain placeholders. Replace them "
            "with truthful information and do not invent achievements."
        ),
    }
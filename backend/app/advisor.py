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


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
MAX_FEEDBACK_ITEMS = 12
MAX_EVIDENCE_LENGTH = 180
WEAK_OPENINGS = {
    "worked": "Describe the specific contribution with a truthful action verb.",
    "helped": "Clarify the contribution without overstating ownership.",
    "responsible": "State the work completed and the outcome where available.",
    "involved": "State the specific contribution and technology used.",
    "participated": "Describe the contribution made to the work.",
}
GENERIC_PHRASES = {
    "hardworking",
    "team player",
    "quick learner",
    "passionate",
    "good communication skills",
    "various tasks",
    "many projects",
    "excellent skills",
}
SECTION_LABELS = {
    "summary": "Summary",
    "skills": "Skills",
    "experience": "Experience",
    "projects": "Projects",
    "education": "Education",
    "certifications": "Certifications",
    "achievements": "Achievements",
    "contact": "Contact information",
}


def redact_evidence(value: str) -> str:
    """Return a short excerpt without contact or address-like data."""

    redacted = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[email removed]",
        value,
    )
    redacted = re.sub(
        r"(?:\+?\d[\d\s().-]{7,}\d)",
        "[phone removed]",
        redacted,
    )
    redacted = re.sub(r"https?://\S+|www\.\S+", "[link removed]", redacted)
    redacted = re.sub(
        r"\b\d{1,5}\s+[A-Za-z][A-Za-z .'-]{2,}\s(?:street|st|road|rd|avenue|ave|lane|ln)\b",
        "[address removed]",
        redacted,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", redacted).strip()[:MAX_EVIDENCE_LENGTH]


def make_issue(
    issue_id: str,
    category: str,
    priority: str,
    message: str,
    evidence: str | None = None,
) -> dict[str, str]:
    """Create one stable, JSON-safe feedback issue."""

    issue = {
        "id": issue_id,
        "category": category,
        "priority": priority,
        "message": message,
    }
    if evidence:
        issue["evidence"] = redact_evidence(evidence)
    return issue


def stable_issues(issues: list[dict[str, str]]) -> list[dict[str, str]]:
    """Deduplicate and order issues independently of input order."""

    unique = {item["id"]: item for item in issues}
    return sorted(
        unique.values(),
        key=lambda item: (
            PRIORITY_ORDER.get(item["priority"], 3),
            item["category"],
            item["id"],
        ),
    )[:MAX_FEEDBACK_ITEMS]


def get_nonempty_lines(text: str) -> list[str]:
    """
    Return cleaned, non-empty resume lines.
    """

    return [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
        if line.strip()
    ]


def normalized_text(value: str) -> str:
    """Normalize text for deterministic, lightweight comparisons."""

    return re.sub(r"[^a-z0-9+#.]+", " ", value.lower()).strip()


def extract_feedback_bullets(
    parsed_data: dict[str, Any],
    resume_text: str,
) -> list[dict[str, str]]:
    """Extract bounded experience/project bullets with a paragraph fallback."""

    sections = parsed_data.get("sections", {})
    bullets: list[dict[str, str]] = []

    for section_name in ("experience", "projects"):
        for line in get_nonempty_lines(sections.get(section_name, "")):
            cleaned = re.sub(r"^[\u2022•*\-–—\d.)\s]+", "", line).strip()
            if len(cleaned.split()) >= 3:
                bullets.append({"section_name": section_name, "text": cleaned})

    if not bullets:
        for line in get_nonempty_lines(resume_text):
            if is_probable_heading(line) or re.search(r"@|https?://|\+?\d{10,}", line):
                continue
            if len(line.split()) >= 6:
                bullets.append({"section_name": "resume", "text": line})

    return bullets[:MAX_FEEDBACK_ITEMS]


def analyze_bullets(
    parsed_data: dict[str, Any],
    resume_text: str,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Analyze project/experience bullets without rewriting their claims."""

    bullets = extract_feedback_bullets(parsed_data, resume_text)
    results: list[dict[str, Any]] = []
    all_issues: list[dict[str, str]] = []
    opening_counts: Counter[str] = Counter()

    for index, bullet in enumerate(bullets, start=1):
        text = bullet["text"]
        words = text.split()
        first_match = re.match(r"^[^A-Za-z]*([A-Za-z]+)", text)
        first_word = first_match.group(1).lower() if first_match else ""
        opening_counts[first_word] += 1 if first_word else 0
        issues: list[dict[str, str]] = []
        bullet_id = f"bullet-{index:02d}"

        if first_word in WEAK_OPENINGS:
            issues.append(make_issue(
                f"{bullet_id}-weak-opening",
                "action_verbs",
                "medium",
                WEAK_OPENINGS[first_word],
                text,
            ))
        elif first_word and first_word not in STRONG_ACTION_VERBS:
            issues.append(make_issue(
                f"{bullet_id}-unclear-opening",
                "action_verbs",
                "low",
                "Consider starting this bullet with a precise action verb when it accurately describes your contribution.",
                text,
            ))

        if re.search(r"\b(?:i|me|my|we|our)\b", text, re.IGNORECASE):
            issues.append(make_issue(
                f"{bullet_id}-first-person",
                "readability",
                "low",
                "Resume bullets are usually clearer without first-person pronouns.",
                text,
            ))
        if len(words) > 42:
            issues.append(make_issue(
                f"{bullet_id}-long",
                "readability",
                "medium",
                "This bullet is long; consider separating the contribution and result into shorter statements.",
                text,
            ))
        if 3 <= len(words) <= 5:
            issues.append(make_issue(
                f"{bullet_id}-short",
                "bullet_detail",
                "medium",
                "This short bullet could include the task, technology, or outcome where truthful.",
                text,
            ))
        if re.search(r"\b(?:improved|increased|reduced|saved|faster|optimized|grew)\b", text, re.IGNORECASE) and not re.search(r"\d", text):
            issues.append(make_issue(
                f"{bullet_id}-quantification",
                "quantification",
                "medium",
                "Add a measured result if you have one; for example, time saved, records handled, or a validated performance change.",
                text,
            ))

        stable = stable_issues(issues)
        all_issues.extend(stable)
        results.append({
            "id": bullet_id,
            "section_name": bullet["section_name"],
            "evidence": redact_evidence(text),
            "issues": stable,
        })

    normalized_counts = Counter(normalized_text(item["text"]) for item in bullets)
    for index, bullet in enumerate(bullets, start=1):
        if normalized_counts[normalized_text(bullet["text"])] > 1:
            all_issues.append(make_issue(
                f"bullet-{index:02d}-duplicate",
                "repetition",
                "medium",
                "This bullet duplicates another statement; combine or differentiate the evidence.",
                bullet["text"],
            ))

    for opening, count in sorted(opening_counts.items()):
        if opening and count >= 3:
            all_issues.append(make_issue(
                f"repeated-opening-{opening}",
                "repetition",
                "low",
                f"The opening verb '{opening}' appears repeatedly; vary wording when it remains accurate.",
            ))

    return results, stable_issues(all_issues)


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


def analyze_content_issues(resume_text: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Find bounded generic, readability, and date-format feedback."""

    content_issues: list[dict[str, str]] = []
    readability_issues: list[dict[str, str]] = []
    lowercase = resume_text.lower()

    for phrase in sorted(GENERIC_PHRASES):
        if phrase in lowercase:
            content_issues.append(make_issue(
                f"generic-{phrase.replace(' ', '-')}",
                "generic_wording",
                "low",
                f"'{phrase}' is more convincing when supported by a concrete example.",
            ))

    for line in get_nonempty_lines(resume_text):
        if len(line.split()) > 55:
            readability_issues.append(make_issue(
                "readability-dense-content",
                "readability",
                "medium",
                "A dense sentence or paragraph may be easier to scan when split into shorter resume-focused statements.",
                line,
            ))
            break
        if re.search(r"[!]{2,}|[?]{2,}", line):
            readability_issues.append(make_issue(
                "readability-excessive-punctuation",
                "readability",
                "low",
                "Use restrained punctuation so technical content remains easy to scan.",
                line,
            ))
            break

    date_styles = set()
    if re.search(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b", lowercase):
        date_styles.add("month-year")
    if re.search(r"\b\d{1,2}/\d{4}\b", resume_text):
        date_styles.add("numeric-month-year")
    if re.search(r"\b\d{4}\s*[-–—]\s*\d{4}\b", resume_text):
        date_styles.add("year-range")
    if len(date_styles) > 1:
        readability_issues.append(make_issue(
            "readability-date-format",
            "readability",
            "low",
            "Use a consistent date style across education, project, and experience entries.",
        ))

    return stable_issues(content_issues), stable_issues(readability_issues)


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

    section_feedback = analyze_section_feedback(parsed_data)
    bullet_feedback, bullet_issues = analyze_bullets(
        parsed_data,
        resume_text,
    )
    content_issues, readability_issues = analyze_content_issues(resume_text)
    contact_feedback = analyze_contact_feedback(parsed_data, resume_text)
    skills_feedback = analyze_skills_feedback(parsed_data)

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

    advanced_issues = stable_issues(
        bullet_issues
        + content_issues
        + readability_issues
        + contact_feedback["issues"]
        + skills_feedback["issues"]
        + [
            issue
            for section in section_feedback
            for issue in section["issues"]
        ]
    )
    priority_actions = [
        {
            "id": issue["id"],
            "priority": issue["priority"],
            "category": issue["category"],
            "action": issue["message"],
        }
        for issue in advanced_issues[:3]
    ]
    strengths = [
        strength
        for section in section_feedback
        for strength in section["strengths"]
    ][:5] + contact_feedback["strengths"][:2]
    overall_feedback_summary = (
        "The feedback highlights the most important structure, writing, and evidence opportunities found in this resume."
        if advanced_issues
        else "No major deterministic writing or structure issues were detected in the reviewed content."
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
        "overall_feedback_summary": overall_feedback_summary,
        "section_feedback": section_feedback,
        "bullet_feedback": bullet_feedback,
        "content_issues": content_issues,
        "readability_issues": readability_issues,
        "action_verb_feedback": {
            "strong_action_percentage": action_result[
                "action_verb_percentage"
            ],
            "issues": [
                issue
                for issue in bullet_issues
                if issue["category"] == "action_verbs"
            ],
        },
        "quantification_opportunities": [
            issue
            for issue in bullet_issues
            if issue["category"] == "quantification"
        ],
        "repetition_issues": [
            issue
            for issue in bullet_issues
            if issue["category"] == "repetition"
        ],
        "contact_information_feedback": contact_feedback,
        "skills_feedback": skills_feedback,
        "priority_actions": priority_actions,
        "strengths": strengths,
        "limitations": [
            "Feedback is rule-based and cannot verify whether a listed skill or claim is accurate.",
            "Projects, coursework, internships, and research can demonstrate experience for students and entry-level candidates.",
        ],
        "disclaimer": (
            "Feedback is deterministic and advisory. Verify every suggestion, use only truthful details, and do not invent achievements or metrics."
        ),
    }


def analyze_section_feedback(
    parsed_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return concise section feedback while treating projects as experience evidence."""

    sections = parsed_data.get("sections", {})
    has_projects = bool(sections.get("projects", "").strip())
    feedback: list[dict[str, Any]] = []

    for section_name in (
        "summary", "skills", "experience", "projects", "education",
        "certifications", "achievements",
    ):
        content = sections.get(section_name, "").strip()
        issues: list[dict[str, str]] = []
        strengths: list[str] = []
        suggestions: list[str] = []
        detected = bool(content)

        if detected:
            strengths.append(f"{SECTION_LABELS[section_name]} is clearly labeled.")
            if section_name in {"experience", "projects"} and len(content.split()) < 20:
                issues.append(make_issue(
                    f"section-{section_name}-brief",
                    "sections",
                    "medium",
                    f"Add more concrete detail to the {SECTION_LABELS[section_name].lower()} section where available.",
                    content,
                ))
        elif section_name == "experience" and has_projects:
            suggestions.append("Projects can demonstrate relevant experience for entry-level resumes; add internships or employment only when applicable.")
        elif section_name in {"certifications", "achievements"}:
            suggestions.append(f"Include {SECTION_LABELS[section_name].lower()} only when you have relevant evidence.")
        elif section_name == "summary":
            suggestions.append("A short summary can help when it clarifies your target area and demonstrated skills.")
        else:
            priority = "high" if section_name in {"skills", "education"} else "medium"
            issues.append(make_issue(
                f"section-{section_name}-missing",
                "sections",
                priority,
                f"Consider adding a clearly labeled {SECTION_LABELS[section_name].lower()} section if it reflects your background.",
            ))

        feedback.append({
            "section_name": section_name,
            "detected": detected,
            "strengths": strengths,
            "issues": stable_issues(issues),
            "suggestions": suggestions,
            "priority": (
                stable_issues(issues)[0]["priority"] if issues else "low"
            ),
            "evidence": redact_evidence(content) if content else None,
        })

    return feedback


def analyze_contact_feedback(
    parsed_data: dict[str, Any],
    resume_text: str,
) -> dict[str, Any]:
    """Provide privacy-conscious contact feedback without returning values."""

    issues: list[dict[str, str]] = []
    strengths: list[str] = []
    links = parsed_data.get("links", {})

    if parsed_data.get("email"):
        strengths.append("An email address was detected.")
    else:
        issues.append(make_issue("contact-email-missing", "contact", "high", "Add a professional email address."))
    if parsed_data.get("phone"):
        strengths.append("A phone number was detected.")
    else:
        issues.append(make_issue("contact-phone-missing", "contact", "medium", "Consider adding a phone number if appropriate for your application."))
    if not links.get("linkedin"):
        issues.append(make_issue("contact-linkedin-optional", "contact", "low", "Consider adding a LinkedIn profile if it strengthens your professional context."))
    if not (links.get("github") or links.get("portfolio")):
        issues.append(make_issue("contact-work-sample-optional", "contact", "low", "For technical roles, consider linking relevant work samples when available."))
    if re.search(r"\b\d{1,5}\s+[^\n]{3,40}\s(?:street|st|road|rd|avenue|ave|lane|ln)\b", resume_text, re.IGNORECASE):
        issues.append(make_issue("contact-precise-address", "privacy", "medium", "Avoid including a precise residential street address unless it is required."))

    return {"strengths": strengths, "issues": stable_issues(issues)}


def analyze_skills_feedback(parsed_data: dict[str, Any]) -> dict[str, Any]:
    """Identify duplicate or unsupported-by-section skill presentation safely."""

    skills = parsed_data.get("skills", {}).get("all", [])
    sections = parsed_data.get("sections", {})
    demonstrated_text = " ".join(
        [sections.get("experience", ""), sections.get("projects", "")]
    ).lower()
    normalized = [normalized_text(skill) for skill in skills]
    duplicates = sorted({skill for skill, count in Counter(normalized).items() if count > 1})
    issues: list[dict[str, str]] = []

    if duplicates:
        issues.append(make_issue("skills-duplicates", "skills", "low", "Remove duplicate skills so the skills section is easier to scan."))

    not_demonstrated = [
        skill for skill in skills
        if normalized_text(skill) and normalized_text(skill) not in demonstrated_text
    ][:5]
    if not_demonstrated:
        issues.append(make_issue(
            "skills-not-demonstrated",
            "skills",
            "low",
            "Consider demonstrating listed skills in a project or experience bullet where truthful.",
        ))

    return {
        "detected_skill_count": len(skills),
        "not_demonstrated_skills": not_demonstrated,
        "issues": stable_issues(issues),
    }

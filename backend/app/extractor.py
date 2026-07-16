import json
import re
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent.parent
SKILLS_FILE = BASE_DIR / "data" / "skills.json"


SECTION_HEADINGS = {
    "summary": [
        "summary",
        "professional summary",
        "career summary",
        "profile",
        "objective",
        "career objective",
        "about me",
    ],
    "skills": [
        "skills",
        "technical skills",
        "core skills",
        "key skills",
        "technologies",
        "technical expertise",
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "internship",
        "internships",
    ],
    "education": [
        "education",
        "academic background",
        "academic qualifications",
        "educational qualifications",
    ],
    "projects": [
        "projects",
        "academic projects",
        "personal projects",
        "major projects",
        "project experience",
    ],
    "certifications": [
        "certifications",
        "certificates",
        "courses",
        "training",
    ],
    "achievements": [
        "achievements",
        "awards",
        "honors",
        "accomplishments",
    ],
}


def load_skills() -> dict[str, list[str]]:
    """
    Load skills from the JSON taxonomy file.
    """

    try:
        with SKILLS_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError as error:
        raise RuntimeError(
            f"Skills file was not found at: {SKILLS_FILE}"
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"The skills JSON file is invalid: {error}"
        ) from error


def normalize_whitespace(value: str) -> str:
    """
    Replace repeated whitespace with a single space.
    """

    return re.sub(r"\s+", " ", value).strip()


def extract_email(text: str) -> Optional[str]:
    """
    Extract the first valid-looking email address.
    """

    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    match = re.search(email_pattern, text)

    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    """
    Extract an Indian or international-style phone number.
    """

    phone_patterns = [
        r"(?:\+91[\s-]?)?[6-9]\d{9}",
        r"\+\d{1,3}[\s-]?(?:\d[\s-]?){8,14}\d",
        r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
    ]

    for pattern in phone_patterns:
        match = re.search(pattern, text)

        if match:
            return normalize_whitespace(match.group(0))

    return None


def extract_urls(text: str) -> list[str]:
    """
    Extract URLs from the resume text.
    """

    url_pattern = (
        r"(?:(?:https?://)|(?:www\.))"
        r"[A-Za-z0-9.-]+"
        r"(?:\.[A-Za-z]{2,})"
        r"(?:/[^\s]*)?"
    )

    urls = re.findall(url_pattern, text, flags=re.IGNORECASE)

    cleaned_urls = []

    for url in urls:
        cleaned_url = url.rstrip(".,;:)]}")

        if cleaned_url not in cleaned_urls:
            cleaned_urls.append(cleaned_url)

    return cleaned_urls


def classify_urls(urls: list[str]) -> dict[str, Optional[str]]:
    """
    Identify LinkedIn, GitHub and portfolio links.
    """

    result = {
        "linkedin": None,
        "github": None,
        "portfolio": None,
    }

    for url in urls:
        lowercase_url = url.lower()

        if "linkedin.com" in lowercase_url and result["linkedin"] is None:
            result["linkedin"] = url

        elif "github.com" in lowercase_url and result["github"] is None:
            result["github"] = url

        elif result["portfolio"] is None:
            result["portfolio"] = url

    return result


def extract_name(text: str) -> Optional[str]:
    """
    Estimate the candidate's name from the first few resume lines.

    This is a heuristic and will be improved later using NLP.
    """

    excluded_words = {
        "resume",
        "curriculum vitae",
        "cv",
        "developer",
        "engineer",
        "student",
        "email",
        "phone",
        "linkedin",
        "github",
        "profile",
        "summary",
        "objective",
    }

    lines = [
        normalize_whitespace(line)
        for line in text.splitlines()
        if normalize_whitespace(line)
    ]

    for line in lines[:8]:
        lowercase_line = line.lower()

        if any(word in lowercase_line for word in excluded_words):
            continue

        if "@" in line or "http" in lowercase_line or "www." in lowercase_line:
            continue

        if any(character.isdigit() for character in line):
            continue

        words = line.split()

        if 2 <= len(words) <= 4:
            valid_words = all(
                re.fullmatch(r"[A-Za-z.'-]+", word)
                for word in words
            )

            if valid_words:
                return line.title()

    return None


def skill_exists(skill: str, lowercase_text: str) -> bool:
    """
    Check whether a skill exists as a complete phrase.

    This reduces false matches such as finding 'c' inside another word.
    """

    escaped_skill = re.escape(skill.lower())

    pattern = rf"(?<![A-Za-z0-9]){escaped_skill}(?![A-Za-z0-9])"

    return bool(re.search(pattern, lowercase_text))


def extract_skills(text: str) -> dict[str, list[str]]:
    """
    Extract categorized skills from resume text.
    """

    skill_taxonomy = load_skills()
    lowercase_text = text.lower()

    extracted_skills: dict[str, list[str]] = {}

    for category, skills in skill_taxonomy.items():
        matched_skills = []

        # Longer phrases are checked before shorter variations.
        sorted_skills = sorted(skills, key=len, reverse=True)

        for skill in sorted_skills:
            if skill_exists(skill, lowercase_text):
                matched_skills.append(skill)

        if matched_skills:
            extracted_skills[category] = sorted(
                set(matched_skills),
                key=str.lower,
            )

    return extracted_skills


def flatten_skills(
    categorized_skills: dict[str, list[str]]
) -> list[str]:
    """
    Convert categorized skills into one unique list.
    """

    all_skills = []

    for skills in categorized_skills.values():
        for skill in skills:
            if skill not in all_skills:
                all_skills.append(skill)

    return sorted(all_skills, key=str.lower)


def normalize_heading(line: str) -> str:
    """
    Normalize a possible section heading.
    """

    normalized = line.lower().strip()
    normalized = re.sub(r"[:\-–—]+$", "", normalized)
    normalized = re.sub(r"[^a-z\s]", "", normalized)
    normalized = normalize_whitespace(normalized)

    return normalized


def identify_section(line: str) -> Optional[str]:
    """
    Determine whether a line is a known section heading.
    """

    normalized_line = normalize_heading(line)

    for section_name, headings in SECTION_HEADINGS.items():
        if normalized_line in headings:
            return section_name

    return None


def extract_sections(text: str) -> dict[str, str]:
    """
    Split resume text into recognized sections.
    """

    sections: dict[str, list[str]] = {}
    current_section: Optional[str] = None

    for original_line in text.splitlines():
        line = original_line.strip()

        if not line:
            continue

        detected_section = identify_section(line)

        if detected_section:
            current_section = detected_section
            sections.setdefault(current_section, [])
            continue

        if current_section:
            sections[current_section].append(line)

    return {
        section_name: "\n".join(content).strip()
        for section_name, content in sections.items()
        if content
    }


def extract_education_lines(text: str) -> list[str]:
    """
    Find lines that are likely related to education.
    """

    education_keywords = [
        "b.tech",
        "btech",
        "bachelor",
        "master",
        "m.tech",
        "mtech",
        "mba",
        "bca",
        "mca",
        "b.sc",
        "m.sc",
        "computer science",
        "university",
        "college",
        "school",
        "cgpa",
        "percentage",
        "cbse",
        "icse",
        "graduation",
    ]

    matched_lines = []

    for line in text.splitlines():
        cleaned_line = normalize_whitespace(line)
        lowercase_line = cleaned_line.lower()

        if not cleaned_line:
            continue

        if any(keyword in lowercase_line for keyword in education_keywords):
            if cleaned_line not in matched_lines:
                matched_lines.append(cleaned_line)

    return matched_lines


def extract_resume_information(text: str) -> dict:
    """
    Run all resume information extractors.
    """

    urls = extract_urls(text)
    categorized_skills = extract_skills(text)

    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "links": classify_urls(urls),
        "skills": {
            "all": flatten_skills(categorized_skills),
            "by_category": categorized_skills,
            "total_detected": len(flatten_skills(categorized_skills)),
        },
        "education": extract_education_lines(text),
        "sections": extract_sections(text),
    }
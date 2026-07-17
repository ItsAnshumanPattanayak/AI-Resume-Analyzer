import json
import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from app.extractor import extract_skills, flatten_skills
from app.config import settings
from app.semantic import encode_texts


BASE_DIR = Path(__file__).resolve().parent.parent
ROLE_PROFILES_FILE = BASE_DIR / "data" / "role_profiles.json"


SKILL_ALIASES = {
    "artificial intelligence": {
        "artificial intelligence",
        "ai",
    },
    "machine learning": {
        "machine learning",
        "ml",
    },
    "natural language processing": {
        "natural language processing",
        "nlp",
    },
    "large language models": {
        "large language models",
        "llm",
        "llms",
    },
    "retrieval augmented generation": {
        "retrieval augmented generation",
        "rag",
    },
    "object-oriented programming": {
        "object-oriented programming",
        "object oriented programming",
        "oop",
    },
    "continuous integration and deployment": {
        "continuous integration and deployment",
        "continuous integration",
        "continuous deployment",
        "ci/cd",
    },
}


SKILL_MATCH_WEIGHT = 0.70
SEMANTIC_MATCH_WEIGHT = 0.30
MAX_EXPLANATION_SKILLS = 3


@lru_cache(maxsize=1)
def load_role_profiles() -> dict[str, dict[str, Any]]:
    """
    Load job-role profiles from the JSON file.
    """

    try:
        with ROLE_PROFILES_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            role_profiles = json.load(file)

    except FileNotFoundError as error:
        raise RuntimeError(
            f"Role profiles file was not found: "
            f"{ROLE_PROFILES_FILE}"
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Role profiles JSON is invalid: {error}"
        ) from error

    if not isinstance(role_profiles, dict):
        raise RuntimeError(
            "Role profiles must be stored as a JSON object."
        )

    return role_profiles


def normalize_skill(skill: str) -> str:
    """
    Normalize a skill for comparison.
    """

    return " ".join(
        skill.lower().strip().split()
    )


NORMALIZED_SKILL_ALIASES = {
    normalize_skill(alias): canonical_name
    for canonical_name, aliases in SKILL_ALIASES.items()
    for alias in aliases
}


def canonicalize_skill(skill: str) -> str:
    """
    Convert aliases such as ML and machine learning
    into one canonical representation.
    """

    normalized_skill = normalize_skill(skill)

    return NORMALIZED_SKILL_ALIASES.get(
        normalized_skill,
        normalized_skill,
    )


def unique_skills(
    skills: list[str],
) -> list[str]:
    """Return case-insensitive, alias-aware unique skills."""

    unique_skill_map: dict[str, str] = {}

    for skill in skills:
        normalized_skill = canonicalize_skill(skill)
        if normalized_skill and normalized_skill not in unique_skill_map:
            unique_skill_map[normalized_skill] = skill.strip()

    return sorted(
        unique_skill_map.values(),
        key=lambda item: (item.casefold(), item),
    )


def bounded_percentage(value: float) -> float:
    """Round a percentage while keeping it within valid bounds."""

    return round(max(0.0, min(float(value), 100.0)), 2)


def extract_candidate_skills(
    resume_text: str,
) -> list[str]:
    """
    Extract a flattened list of candidate skills.
    """

    categorized_skills = extract_skills(resume_text)

    return flatten_skills(categorized_skills)


def calculate_role_skill_match(
    candidate_skills: list[str],
    required_skills: list[str],
) -> dict[str, Any]:
    """
    Compare candidate skills with a role's required skills.
    """

    candidate_skill_map = {
        canonicalize_skill(skill): skill
        for skill in unique_skills(candidate_skills)
    }

    required_skill_map: dict[str, str] = {}
    required_skill_keys: list[str] = []
    for skill in required_skills:
        canonical_skill = canonicalize_skill(skill)
        if canonical_skill and canonical_skill not in required_skill_map:
            required_skill_map[canonical_skill] = skill
            required_skill_keys.append(canonical_skill)

    candidate_skill_keys = set(candidate_skill_map)
    required_skill_key_set = set(required_skill_map)

    matched_keys = (
        candidate_skill_keys
        .intersection(required_skill_key_set)
    )

    missing_keys = (
        required_skill_key_set
        .difference(candidate_skill_keys)
    )

    matched_skills = [
        required_skill_map[key]
        for key in required_skill_keys
        if key in matched_keys
    ]

    missing_skills = [
        required_skill_map[key]
        for key in required_skill_keys
        if key in missing_keys
    ]

    candidate_relevant_skills = [
        candidate_skill_map[key]
        for key in required_skill_keys
        if key in matched_keys
    ]

    if required_skill_keys:
        skill_match_percentage = (
            len(matched_keys)
            / len(required_skill_keys)
        ) * 100
    else:
        skill_match_percentage = 0.0

    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "candidate_relevant_skills": candidate_relevant_skills,
        "matched_count": len(matched_skills),
        "required_count": len(required_skill_keys),
        "missing_count": len(missing_skills),
        "skill_match_percentage": bounded_percentage(skill_match_percentage),
    }


def build_role_texts(
    role_profiles: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str]]:
    role_names = list(role_profiles)
    role_texts = [
        (
            f"{role_name}. {role_profiles[role_name].get('description', '')} "
            "Required skills: "
            f"{', '.join(role_profiles[role_name].get('required_skills', []))}"
        )
        for role_name in role_names
    ]
    return role_names, role_texts


def role_profile_fingerprint(
    role_profiles: dict[str, dict[str, Any]],
) -> str:
    serialized = json.dumps(
        role_profiles,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


@lru_cache(maxsize=4)
def get_static_role_embeddings(
    model_name: str,
    source_fingerprint: str,
) -> tuple[tuple[str, ...], np.ndarray]:
    """Encode static role references once per model and source version."""

    del model_name, source_fingerprint
    role_names, role_texts = build_role_texts(load_role_profiles())
    embeddings = encode_texts(role_texts)
    embeddings.setflags(write=False)
    return tuple(role_names), embeddings


def reset_recommender_caches() -> None:
    load_role_profiles.cache_clear()
    get_static_role_embeddings.cache_clear()


def calculate_role_semantic_scores(
    resume_text: str,
    role_profiles: dict[str, dict[str, Any]],
) -> dict[str, float]:
    """
    Calculate semantic similarity between the resume
    and every role description.
    """

    if not resume_text.strip():
        return {
            role_name: 0.0
            for role_name in role_profiles
        }

    resume_embedding = encode_texts([resume_text])[0]
    role_names, role_embeddings = get_static_role_embeddings(
        settings.semantic_model_name,
        role_profile_fingerprint(role_profiles),
    )

    similarities = np.dot(
        role_embeddings,
        resume_embedding,
    )

    semantic_scores = {}

    for role_name, similarity in zip(
        role_names,
        similarities,
    ):
        bounded_similarity = max(
            0.0,
            min(float(similarity), 1.0),
        )

        semantic_scores[role_name] = round(
            bounded_similarity * 100,
            2,
        )

    return semantic_scores


def get_recommendation_level(
    score: float,
) -> str:
    """
    Convert a numeric role score into a readable level.
    """

    if score >= 75:
        return "Strong fit"

    if score >= 60:
        return "Good fit"

    if score >= 45:
        return "Potential fit"

    if score >= 30:
        return "Developing fit"

    return "Low fit"


def semantic_alignment_label(semantic_score: float) -> str:
    """Describe a measured semantic score without making a hiring claim."""

    if semantic_score >= 70:
        return "strong semantic alignment"
    if semantic_score >= 40:
        return "moderate semantic alignment"
    return "limited semantic alignment"


def build_score_components(
    skill_score: float,
    semantic_score: float,
) -> dict[str, Any]:
    """Build the exact, rounded values used for role ranking."""

    exact_skill_score = bounded_percentage(skill_score)
    bounded_semantic_score = bounded_percentage(semantic_score)
    exact_weighted_score = round(
        exact_skill_score * SKILL_MATCH_WEIGHT,
        2,
    )
    semantic_weighted_score = round(
        bounded_semantic_score * SEMANTIC_MATCH_WEIGHT,
        2,
    )
    final_score = bounded_percentage(
        exact_weighted_score + semantic_weighted_score
    )

    return {
        "exact_skill_coverage": {
            "score": exact_skill_score,
            "weight": SKILL_MATCH_WEIGHT,
            "weighted_score": exact_weighted_score,
        },
        "semantic_similarity": {
            "score": bounded_semantic_score,
            "weight": SEMANTIC_MATCH_WEIGHT,
            "weighted_score": semantic_weighted_score,
        },
        "final_score": {"score": final_score},
    }


def build_strengths(
    *,
    matched_skills: list[str],
    required_count: int,
    skill_score: float,
    semantic_score: float,
) -> list[str]:
    """Build concise strengths from measured role-match data."""

    strengths: list[str] = []

    if required_count and skill_score >= 60:
        strengths.append(
            f"Matches {len(matched_skills)} of {required_count} skills associated with this role."
        )

    if matched_skills:
        strengths.append(
            "Relevant skills include "
            + ", ".join(matched_skills[:MAX_EXPLANATION_SKILLS])
            + "."
        )

    if semantic_score >= 70:
        strengths.append(
            "The resume has strong semantic alignment with this role profile."
        )

    return strengths


def build_improvement_areas(
    *,
    missing_skills: list[str],
    skill_score: float,
    semantic_score: float,
) -> list[str]:
    """Build neutral, actionable improvement areas from score inputs."""

    improvement_areas: list[str] = []

    if missing_skills:
        improvement_areas.append(
            "Consider strengthening "
            + ", ".join(missing_skills[:MAX_EXPLANATION_SKILLS])
            + "."
        )

    if skill_score < 40:
        improvement_areas.append(
            "Add evidence of more skills associated with this role where it reflects your experience."
        )

    if semantic_score < 40:
        improvement_areas.append(
            "Describe role-relevant projects or responsibilities more directly."
        )

    return improvement_areas


def build_role_explanation(
    *,
    matched_skills: list[str],
    missing_skills: list[str],
    required_count: int,
    semantic_score: float,
) -> str:
    """Summarize measured recommendation evidence in deterministic prose."""

    if required_count:
        skill_summary = (
            f"Your resume matches {len(matched_skills)} of {required_count} skills associated with this role."
        )
    else:
        skill_summary = "This role profile does not define required skills."

    explanation_parts = [
        skill_summary,
        "The resume has "
        + semantic_alignment_label(semantic_score)
        + " with this role profile.",
    ]

    if matched_skills:
        explanation_parts.append(
            "Key matches: "
            + ", ".join(matched_skills[:MAX_EXPLANATION_SKILLS])
            + "."
        )

    if missing_skills:
        explanation_parts.append(
            "Consider strengthening "
            + ", ".join(missing_skills[:MAX_EXPLANATION_SKILLS])
            + "."
        )

    return " ".join(explanation_parts)


def build_role_reason(
    role_name: str,
    matched_skills: list[str],
    missing_skills: list[str],
    semantic_score: float,
) -> str:
    """
    Explain why a role was recommended.
    """

    reasons = []

    if matched_skills:
        reasons.append(
            "Matched skills include "
            + ", ".join(matched_skills[:6])
            + "."
        )
    else:
        reasons.append(
            "Few direct required skills were detected."
        )

    if semantic_score >= 60:
        reasons.append(
            "The candidate's resume content is semantically "
            "aligned with this role."
        )
    elif semantic_score >= 40:
        reasons.append(
            "The resume has partial content alignment "
            "with this role."
        )
    else:
        reasons.append(
            "The resume currently has limited content "
            "alignment with this role."
        )

    if missing_skills:
        reasons.append(
            "Important skills to develop include "
            + ", ".join(missing_skills[:5])
            + "."
        )

    return " ".join(reasons)


def recommend_job_roles(
    resume_text: str,
    top_n: int = 5,
    candidate_skills: list[str] | None = None,
) -> dict[str, Any]:
    """
    Recommend suitable job roles based on candidate skills
    and semantic resume-role similarity.
    """

    if not resume_text.strip():
        raise ValueError(
            "Resume text is required for role recommendation."
        )

    if not 1 <= top_n <= 10:
        raise ValueError(
            "top_n must be between 1 and 10."
        )

    role_profiles = load_role_profiles()

    if candidate_skills is None:
        candidate_skills = extract_candidate_skills(
            resume_text
        )

    candidate_skills = unique_skills(candidate_skills)

    semantic_scores = calculate_role_semantic_scores(
        resume_text=resume_text,
        role_profiles=role_profiles,
    )

    recommendations = []

    for role_name, profile in role_profiles.items():
        required_skills = profile.get(
            "required_skills",
            [],
        )

        skill_result = calculate_role_skill_match(
            candidate_skills=candidate_skills,
            required_skills=required_skills,
        )

        semantic_score = semantic_scores.get(
            role_name,
            0.0,
        )

        score_components = build_score_components(
            skill_result["skill_match_percentage"],
            semantic_score,
        )
        overall_score = score_components["final_score"]["score"]
        strengths = build_strengths(
            matched_skills=skill_result["matched_skills"],
            required_count=skill_result["required_count"],
            skill_score=skill_result["skill_match_percentage"],
            semantic_score=semantic_score,
        )
        improvement_areas = build_improvement_areas(
            missing_skills=skill_result["missing_skills"],
            skill_score=skill_result["skill_match_percentage"],
            semantic_score=semantic_score,
        )

        recommendations.append(
            {
                "role": role_name,
                "overall_match_percentage": overall_score,
                "recommendation_level": (
                    get_recommendation_level(
                        overall_score
                    )
                ),
                "skill_match_percentage": (
                    skill_result[
                        "skill_match_percentage"
                    ]
                ),
                "exact_skill_match_percentage": (
                    skill_result[
                        "skill_match_percentage"
                    ]
                ),
                "semantic_match_percentage": (
                    semantic_score
                ),
                "matched_skills": (
                    skill_result["matched_skills"]
                ),
                "missing_skills": (
                    skill_result["missing_skills"]
                ),
                "candidate_relevant_skills": (
                    skill_result[
                        "candidate_relevant_skills"
                    ]
                ),
                "total_required_skills": (
                    skill_result["required_count"]
                ),
                "matched_skill_count": (
                    skill_result["matched_count"]
                ),
                "missing_skill_count": (
                    skill_result["missing_count"]
                ),
                "score_components": score_components,
                "strengths": strengths,
                "improvement_areas": improvement_areas,
                "explanation": build_role_explanation(
                    matched_skills=skill_result[
                        "matched_skills"
                    ],
                    missing_skills=skill_result[
                        "missing_skills"
                    ],
                    required_count=skill_result[
                        "required_count"
                    ],
                    semantic_score=semantic_score,
                ),
                "role_description": profile.get(
                    "description",
                    "",
                ),
                "reason": build_role_reason(
                    role_name=role_name,
                    matched_skills=skill_result[
                        "matched_skills"
                    ],
                    missing_skills=skill_result[
                        "missing_skills"
                    ],
                    semantic_score=semantic_score,
                ),
            }
        )

    recommendations.sort(
        key=lambda item: (
            -item["overall_match_percentage"],
            -item["skill_match_percentage"],
            -item["semantic_match_percentage"],
            item["role"].casefold(),
        ),
    )

    limited_recommendations = recommendations[:top_n]

    best_role = (
        limited_recommendations[0]
        if limited_recommendations
        else None
    )

    return {
        "candidate_skills": candidate_skills,
        "total_candidate_skills": len(
            candidate_skills
        ),
        "scoring_weights": {
            "skills": SKILL_MATCH_WEIGHT,
            "semantic_similarity": SEMANTIC_MATCH_WEIGHT,
        },
        "best_role": best_role,
        "recommended_roles": (
            limited_recommendations
        ),
        "roles_evaluated": len(role_profiles),
    }

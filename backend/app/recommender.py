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
        for skill in candidate_skills
    }

    required_skill_map = {
        canonicalize_skill(skill): skill
        for skill in required_skills
    }

    candidate_skill_keys = set(candidate_skill_map)
    required_skill_keys = set(required_skill_map)

    matched_keys = (
        candidate_skill_keys
        .intersection(required_skill_keys)
    )

    missing_keys = (
        required_skill_keys
        .difference(candidate_skill_keys)
    )

    matched_skills = sorted(
        [
            required_skill_map[key]
            for key in matched_keys
        ],
        key=str.lower,
    )

    missing_skills = sorted(
        [
            required_skill_map[key]
            for key in missing_keys
        ],
        key=str.lower,
    )

    if required_skills:
        skill_match_percentage = (
            len(matched_keys)
            / len(required_skill_keys)
        ) * 100
    else:
        skill_match_percentage = 0.0

    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_count": len(matched_skills),
        "required_count": len(required_skill_keys),
        "skill_match_percentage": round(
            skill_match_percentage,
            2,
        ),
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

    semantic_scores = calculate_role_semantic_scores(
        resume_text=resume_text,
        role_profiles=role_profiles,
    )

    recommendations = []

    skill_weight = 0.70
    semantic_weight = 0.30

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

        overall_score = (
            skill_result["skill_match_percentage"]
            * skill_weight
            + semantic_score
            * semantic_weight
        )

        overall_score = round(
            max(0.0, min(overall_score, 100.0)),
            2,
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
                "semantic_match_percentage": (
                    semantic_score
                ),
                "matched_skills": (
                    skill_result["matched_skills"]
                ),
                "missing_skills": (
                    skill_result["missing_skills"]
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
            "skills": skill_weight,
            "semantic_similarity": semantic_weight,
        },
        "best_role": best_role,
        "recommended_roles": (
            limited_recommendations
        ),
        "roles_evaluated": len(role_profiles),
    }

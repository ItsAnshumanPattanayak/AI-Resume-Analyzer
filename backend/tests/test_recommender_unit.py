import numpy as np
import pytest

from app import recommender
from app.schemas import RoleRecommendationItem


@pytest.fixture(autouse=True)
def clear_recommender_state():
    recommender.reset_recommender_caches()
    yield
    recommender.reset_recommender_caches()


def test_static_role_embeddings_are_reused(monkeypatch) -> None:
    encode_calls = 0

    def fake_encode(texts):
        nonlocal encode_calls
        encode_calls += 1
        return np.ones((len(texts), 3), dtype=np.float32)

    monkeypatch.setattr(recommender, "encode_texts", fake_encode)
    profiles = recommender.load_role_profiles()
    fingerprint = recommender.role_profile_fingerprint(profiles)

    first = recommender.get_static_role_embeddings("model", fingerprint)
    second = recommender.get_static_role_embeddings("model", fingerprint)

    assert first is second
    assert encode_calls == 1


def test_recommendations_are_bounded_unique_and_deterministic(monkeypatch) -> None:
    monkeypatch.setattr(
        recommender,
        "calculate_role_semantic_scores",
        lambda resume_text, role_profiles: {
            role_name: 50.0 for role_name in role_profiles
        },
    )

    skills = ["python", "fastapi", "sql"]
    first = recommender.recommend_job_roles("synthetic resume", 5, skills)
    second = recommender.recommend_job_roles("synthetic resume", 5, skills)

    assert first == second
    roles = [item["role"] for item in first["recommended_roles"]]
    assert len(roles) == len(set(roles))
    scores = [item["overall_match_percentage"] for item in first["recommended_roles"]]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= score <= 100 for score in scores)


@pytest.mark.parametrize("top_n", [0, 11])
def test_top_n_boundaries(top_n) -> None:
    with pytest.raises(ValueError, match="between 1 and 10"):
        recommender.recommend_job_roles("synthetic resume", top_n)


def test_empty_resume_is_rejected() -> None:
    with pytest.raises(ValueError, match="Resume text is required"):
        recommender.recommend_job_roles("", 5)


def test_explainable_score_components_reconstruct_ranking(
    monkeypatch,
) -> None:
    profiles = {
        "Example Engineer": {
            "description": "Example role.",
            "required_skills": [
                "Python",
                "Machine Learning",
                "Docker",
            ],
        }
    }
    monkeypatch.setattr(recommender, "load_role_profiles", lambda: profiles)
    monkeypatch.setattr(
        recommender,
        "calculate_role_semantic_scores",
        lambda resume_text, role_profiles: {"Example Engineer": 80.0},
    )

    result = recommender.recommend_job_roles(
        "synthetic resume",
        candidate_skills=["Python", "ML", "python"],
    )
    role = result["best_role"]

    assert role["skill_match_percentage"] == 66.67
    assert role["exact_skill_match_percentage"] == 66.67
    assert role["semantic_match_percentage"] == 80.0
    assert role["overall_match_percentage"] == 70.67
    assert role["score_components"] == {
        "exact_skill_coverage": {
            "score": 66.67,
            "weight": 0.7,
            "weighted_score": 46.67,
        },
        "semantic_similarity": {
            "score": 80.0,
            "weight": 0.3,
            "weighted_score": 24.0,
        },
        "final_score": {"score": 70.67},
    }
    assert role["overall_match_percentage"] == sum(
        component["weighted_score"]
        for component in role["score_components"].values()
        if "weighted_score" in component
    )
    assert role["matched_skills"] == ["Python", "Machine Learning"]
    assert role["candidate_relevant_skills"] == ["Python", "ML"]
    assert role["missing_skills"] == ["Docker"]
    assert role["matched_skill_count"] == 2
    assert role["missing_skill_count"] == 1
    assert role["total_required_skills"] == 3
    assert RoleRecommendationItem.model_validate(role).role == "Example Engineer"


def test_skill_aliases_and_technical_names_are_preserved() -> None:
    result = recommender.calculate_role_skill_match(
        candidate_skills=["c++", "C#", ".net", "node.js", "CI/CD", "AWS", "SQL"],
        required_skills=["C++", "C#", ".NET", "Node.js", "CI/CD", "AWS", "SQL"],
    )

    assert result["matched_skills"] == [
        "C++",
        "C#",
        ".NET",
        "Node.js",
        "CI/CD",
        "AWS",
        "SQL",
    ]
    assert result["missing_skills"] == []
    assert result["skill_match_percentage"] == 100.0


@pytest.mark.parametrize(
    ("semantic_score", "expected_phrase"),
    [
        (80.0, "strong semantic alignment"),
        (50.0, "moderate semantic alignment"),
        (20.0, "limited semantic alignment"),
    ],
)
def test_explanation_wording_is_deterministic(
    monkeypatch,
    semantic_score,
    expected_phrase,
) -> None:
    profiles = {
        "Example Engineer": {
            "description": "Example role.",
            "required_skills": ["Python", "Docker"],
        }
    }
    monkeypatch.setattr(recommender, "load_role_profiles", lambda: profiles)
    monkeypatch.setattr(
        recommender,
        "calculate_role_semantic_scores",
        lambda resume_text, role_profiles: {"Example Engineer": semantic_score},
    )

    first = recommender.recommend_job_roles(
        "synthetic resume",
        candidate_skills=["Python"],
    )["best_role"]
    second = recommender.recommend_job_roles(
        "synthetic resume",
        candidate_skills=["Python"],
    )["best_role"]

    assert first == second
    assert expected_phrase in first["explanation"]
    assert first["improvement_areas"]


def test_role_with_no_required_skills_is_safe(monkeypatch) -> None:
    profiles = {
        "Example Engineer": {
            "description": "Example role.",
            "required_skills": [],
        }
    }
    monkeypatch.setattr(recommender, "load_role_profiles", lambda: profiles)
    monkeypatch.setattr(
        recommender,
        "calculate_role_semantic_scores",
        lambda resume_text, role_profiles: {"Example Engineer": 50.0},
    )

    role = recommender.recommend_job_roles(
        "synthetic resume",
        candidate_skills=[],
    )["best_role"]

    assert role["total_required_skills"] == 0
    assert role["overall_match_percentage"] == 15.0
    assert "does not define required skills" in role["explanation"]


def test_no_detected_skills_has_a_low_explainable_score(monkeypatch) -> None:
    profiles = {
        "Example Engineer": {
            "description": "Example role.",
            "required_skills": ["Python", "Docker"],
        }
    }
    monkeypatch.setattr(recommender, "load_role_profiles", lambda: profiles)
    monkeypatch.setattr(
        recommender,
        "calculate_role_semantic_scores",
        lambda resume_text, role_profiles: {"Example Engineer": 0.0},
    )

    role = recommender.recommend_job_roles(
        "synthetic resume",
        candidate_skills=[],
    )["best_role"]

    assert role["overall_match_percentage"] == 0.0
    assert role["matched_skills"] == []
    assert role["missing_skills"] == ["Python", "Docker"]
    assert role["strengths"] == []
    assert "matches 0 of 2 skills" in role["explanation"]


def test_top_n_larger_than_available_roles_returns_available_roles(
    monkeypatch,
) -> None:
    profiles = {
        "Example Engineer": {
            "description": "Example role.",
            "required_skills": ["Python"],
        }
    }
    monkeypatch.setattr(recommender, "load_role_profiles", lambda: profiles)
    monkeypatch.setattr(
        recommender,
        "calculate_role_semantic_scores",
        lambda resume_text, role_profiles: {"Example Engineer": 50.0},
    )

    result = recommender.recommend_job_roles(
        "synthetic resume",
        top_n=10,
        candidate_skills=[],
    )

    assert len(result["recommended_roles"]) == 1


def test_semantic_failure_remains_explicit(monkeypatch) -> None:
    monkeypatch.setattr(
        recommender,
        "calculate_role_semantic_scores",
        lambda resume_text, role_profiles: (_ for _ in ()).throw(
            RuntimeError("The semantic analysis service is unavailable.")
        ),
    )

    with pytest.raises(RuntimeError, match="semantic analysis service"):
        recommender.recommend_job_roles("synthetic resume", candidate_skills=[])

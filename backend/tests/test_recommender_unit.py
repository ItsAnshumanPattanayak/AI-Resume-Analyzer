import numpy as np
import pytest

from app import recommender


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

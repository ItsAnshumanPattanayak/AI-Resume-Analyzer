import numpy as np
import pytest

from app.semantic import (
    calculate_chunk_matches,
    calculate_cosine_score,
    calculate_document_embedding,
    calculate_semantic_similarity,
    clean_semantic_text,
    convert_similarity_to_percentage,
    create_text_chunks,
    encode_texts,
    get_semantic_model,
    normalize_embedding,
    split_into_sentences,
)


pytestmark = pytest.mark.semantic


def test_clean_semantic_text() -> None:
    text = (
        "Python    developer\r\n"
        "Machine learning engineer.\n\n\n"
        "FastAPI developer."
    )

    cleaned_text = clean_semantic_text(
        text
    )

    assert "Python developer" in cleaned_text
    assert "\r" not in cleaned_text
    assert "\n\n\n" not in cleaned_text
    assert cleaned_text.endswith(
        "FastAPI developer."
    )


def test_clean_empty_semantic_text() -> None:
    assert clean_semantic_text("") == ""


def test_split_into_sentences() -> None:
    text = (
        "Python developer. "
        "Built machine learning systems.\n"
        "Created FastAPI applications."
    )

    sentences = split_into_sentences(
        text
    )

    assert len(sentences) == 3
    assert sentences[0] == (
        "Python developer."
    )
    assert sentences[1] == (
        "Built machine learning systems."
    )
    assert sentences[2] == (
        "Created FastAPI applications."
    )


def test_split_resume_bullet_points() -> None:
    text = (
        "Skills\n"
        "• Python\n"
        "• FastAPI\n"
        "• Machine Learning"
    )

    sentences = split_into_sentences(
        text
    )

    assert "Skills" in sentences
    assert "Python" in sentences
    assert "FastAPI" in sentences
    assert "Machine Learning" in sentences


def test_split_empty_text() -> None:
    assert split_into_sentences("") == []


def test_create_text_chunks() -> None:
    text = (
        "Python developer. "
        "Machine learning engineer. "
        "Created REST APIs using FastAPI. "
        "Worked with SQL databases."
    )

    chunks = create_text_chunks(
        text,
        maximum_words=8,
        overlap_sentences=1,
    )

    assert len(chunks) >= 2

    for chunk in chunks:
        assert isinstance(chunk, str)
        assert chunk.strip()


def test_create_text_chunks_with_no_overlap() -> None:
    text = (
        "Python developer. "
        "Machine learning engineer. "
        "FastAPI backend developer."
    )

    chunks = create_text_chunks(
        text,
        maximum_words=4,
        overlap_sentences=0,
    )

    assert len(chunks) >= 2


def test_create_text_chunks_rejects_invalid_word_limit() -> None:
    with pytest.raises(
        ValueError,
        match="maximum_words",
    ):
        create_text_chunks(
            "Python developer",
            maximum_words=0,
        )


def test_create_text_chunks_rejects_negative_overlap() -> None:
    with pytest.raises(
        ValueError,
        match="overlap_sentences",
    ):
        create_text_chunks(
            "Python developer",
            overlap_sentences=-1,
        )


def test_normalize_embedding() -> None:
    embedding = np.array(
        [3.0, 4.0],
        dtype=np.float32,
    )

    normalized = normalize_embedding(
        embedding
    )

    assert np.isclose(
        np.linalg.norm(normalized),
        1.0,
    )


def test_normalize_zero_embedding() -> None:
    embedding = np.array(
        [0.0, 0.0],
        dtype=np.float32,
    )

    normalized = normalize_embedding(
        embedding
    )

    assert np.array_equal(
        normalized,
        embedding,
    )


def test_calculate_cosine_score_for_identical_vectors() -> None:
    first = np.array(
        [1.0, 2.0, 3.0],
        dtype=np.float32,
    )

    second = np.array(
        [1.0, 2.0, 3.0],
        dtype=np.float32,
    )

    score = calculate_cosine_score(
        first,
        second,
    )

    assert score == pytest.approx(
        1.0,
        abs=1e-6,
    )


def test_calculate_cosine_score_for_orthogonal_vectors() -> None:
    first = np.array(
        [1.0, 0.0],
        dtype=np.float32,
    )

    second = np.array(
        [0.0, 1.0],
        dtype=np.float32,
    )

    score = calculate_cosine_score(
        first,
        second,
    )

    assert score == pytest.approx(
        0.0,
        abs=1e-6,
    )


@pytest.mark.parametrize(
    ("similarity", "expected"),
    [
        (1.0, 100.0),
        (0.75, 75.0),
        (0.0, 0.0),
        (-0.5, 0.0),
        (1.5, 100.0),
    ],
)
def test_convert_similarity_to_percentage(
    similarity: float,
    expected: float,
) -> None:
    result = (
        convert_similarity_to_percentage(
            similarity
        )
    )

    assert result == expected


def test_semantic_model_loads() -> None:
    model = get_semantic_model()

    assert model is not None


def test_encode_texts() -> None:
    embeddings = encode_texts(
        [
            "Python developer",
            "Machine learning engineer",
        ]
    )

    assert isinstance(
        embeddings,
        np.ndarray,
    )

    assert embeddings.shape[0] == 2
    assert embeddings.shape[1] > 0

    first_norm = np.linalg.norm(
        embeddings[0]
    )

    assert first_norm == pytest.approx(
        1.0,
        abs=1e-5,
    )


def test_encode_texts_rejects_empty_list() -> None:
    with pytest.raises(
        ValueError,
        match="At least one",
    ):
        encode_texts([])


def test_calculate_document_embedding() -> None:
    text = (
        "Python developer with FastAPI experience. "
        "Built machine learning applications."
    )

    embedding = (
        calculate_document_embedding(
            text
        )
    )

    assert isinstance(
        embedding,
        np.ndarray,
    )

    assert embedding.ndim == 1
    assert embedding.shape[0] > 0

    assert np.linalg.norm(
        embedding
    ) == pytest.approx(
        1.0,
        abs=1e-5,
    )


def test_document_embedding_rejects_empty_text() -> None:
    with pytest.raises(
        ValueError,
        match="empty text",
    ):
        calculate_document_embedding("")


def test_semantic_similarity_returns_percentage() -> None:
    resume_text = (
        "Python developer with experience in "
        "machine learning, FastAPI, SQL, pandas "
        "and REST API development."
    )

    job_description = (
        "We are hiring a Python machine learning "
        "engineer with FastAPI, SQL and data "
        "processing experience."
    )

    score = calculate_semantic_similarity(
        resume_text=resume_text,
        job_description=job_description,
    )

    assert isinstance(
        score,
        float,
    )

    assert 0.0 <= score <= 100.0
    assert score > 0.0


def test_related_text_scores_higher_than_unrelated_text() -> None:
    resume_text = (
        "Python FastAPI developer with machine "
        "learning and SQL experience."
    )

    related_job = (
        "Python backend engineer required with "
        "FastAPI, machine learning and SQL skills."
    )

    unrelated_job = (
        "Professional chef required for preparing "
        "desserts, managing kitchens and creating menus."
    )

    related_score = (
        calculate_semantic_similarity(
            resume_text,
            related_job,
        )
    )

    unrelated_score = (
        calculate_semantic_similarity(
            resume_text,
            unrelated_job,
        )
    )

    assert related_score > unrelated_score


def test_semantic_similarity_with_empty_resume() -> None:
    score = calculate_semantic_similarity(
        resume_text="",
        job_description=(
            "Python developer required."
        ),
    )

    assert score == 0.0


def test_semantic_similarity_with_empty_job_description() -> None:
    score = calculate_semantic_similarity(
        resume_text=(
            "Python developer."
        ),
        job_description="",
    )

    assert score == 0.0


def test_calculate_chunk_matches() -> None:
    resume_text = (
        "Developed REST APIs using FastAPI and Python. "
        "Built machine learning models using scikit-learn. "
        "Worked with PostgreSQL and SQL databases."
    )

    job_description = (
        "We require a Python developer with FastAPI, "
        "machine learning and SQL experience."
    )

    matches = calculate_chunk_matches(
        resume_text=resume_text,
        job_description=job_description,
        top_k=3,
    )

    assert isinstance(
        matches,
        list,
    )

    assert 1 <= len(matches) <= 3

    for match in matches:
        assert "resume_chunk" in match
        assert (
            "job_description_chunk"
            in match
        )
        assert (
            "similarity_percentage"
            in match
        )

        assert (
            0.0
            <= match[
                "similarity_percentage"
            ]
            <= 100.0
        )


def test_chunk_matches_are_sorted() -> None:
    resume_text = (
        "Python FastAPI developer. "
        "Machine learning engineer. "
        "Graphic design and video editing."
    )

    job_description = (
        "Hiring a Python FastAPI machine "
        "learning developer."
    )

    matches = calculate_chunk_matches(
        resume_text=resume_text,
        job_description=job_description,
        top_k=3,
    )

    scores = [
        match[
            "similarity_percentage"
        ]
        for match in matches
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )


def test_chunk_matches_rejects_invalid_top_k() -> None:
    with pytest.raises(
        ValueError,
        match="top_k",
    ):
        calculate_chunk_matches(
            resume_text=(
                "Python developer"
            ),
            job_description=(
                "Python engineer"
            ),
            top_k=0,
        )


def test_chunk_matches_with_empty_text() -> None:
    matches = calculate_chunk_matches(
        resume_text="",
        job_description=(
            "Python developer required."
        ),
    )

    assert matches == []
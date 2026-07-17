import re
import hashlib
import threading
from collections import OrderedDict

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings


PREPROCESSING_VERSION = "semantic-v1"
_model_lock = threading.Lock()
_inference_lock = threading.Lock()
_cache_lock = threading.Lock()
_semantic_model: SentenceTransformer | None = None
_embedding_cache: OrderedDict[str, np.ndarray] = OrderedDict()


def get_semantic_model() -> SentenceTransformer:
    """
    Load and cache the configured Sentence Transformer model.

    The loading behavior is controlled by:

    SEMANTIC_MODEL_NAME
    SEMANTIC_MODEL_LOCAL_ONLY
    """

    global _semantic_model

    if _semantic_model is not None:
        return _semantic_model

    with _model_lock:
        if _semantic_model is not None:
            return _semantic_model

        try:
            model = SentenceTransformer(
                settings.semantic_model_name,
                local_files_only=(
                    settings.semantic_model_local_only
                ),
            )

        except Exception as error:
            raise RuntimeError(
                "The semantic analysis service is unavailable."
            ) from error

        _semantic_model = model
        return model


def reset_semantic_state() -> None:
    """Clear process-local semantic state for isolated tests."""

    global _semantic_model
    with _model_lock:
        _semantic_model = None
    with _cache_lock:
        _embedding_cache.clear()


def _embedding_key(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return ":".join(
        (
            settings.semantic_model_name,
            PREPROCESSING_VERSION,
            digest,
        )
    )


def semantic_cache_size() -> int:
    with _cache_lock:
        return len(_embedding_cache)


def clean_semantic_text(
    text: str,
) -> str:
    """
    Clean text while preserving punctuation that may help
    interpret sentences and technical terminology.
    """

    if not text:
        return ""

    cleaned_text = (
        text.replace(
            "\r\n",
            "\n",
        )
        .replace(
            "\r",
            "\n",
        )
    )

    cleaned_text = re.sub(
        r"[ \t]+",
        " ",
        cleaned_text,
    )

    cleaned_text = re.sub(
        r"\n{3,}",
        "\n\n",
        cleaned_text,
    )

    return cleaned_text.strip()


def split_into_sentences(
    text: str,
) -> list[str]:
    """
    Split text into approximate sentences and resume lines.

    Resume text often contains bullet points instead of
    grammatically complete sentences, so line breaks are
    also treated as boundaries.
    """

    cleaned_text = clean_semantic_text(
        text
    )

    if not cleaned_text:
        return []

    parts = re.split(
        (
            r"(?<=[.!?])\s+"
            r"|\n+"
            r"|(?:\s*[•▪●◦]\s*)"
        ),
        cleaned_text,
    )

    sentences: list[str] = []

    for part in parts:
        cleaned_part = part.strip(
            " -–—•▪●◦\t"
        )

        if cleaned_part:
            sentences.append(
                cleaned_part
            )

    return sentences


def create_text_chunks(
    text: str,
    maximum_words: int = 120,
    overlap_sentences: int = 1,
) -> list[str]:
    """
    Divide long text into smaller overlapping chunks.

    Args:
        text:
            Complete resume or job-description text.

        maximum_words:
            Approximate maximum words per chunk.

        overlap_sentences:
            Number of sentences shared between
            consecutive chunks.

    Returns:
        A list of text chunks.
    """

    if maximum_words < 1:
        raise ValueError(
            "maximum_words must be at least 1."
        )

    if overlap_sentences < 0:
        raise ValueError(
            "overlap_sentences cannot be negative."
        )

    sentences = split_into_sentences(
        text
    )

    if not sentences:
        return []

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_word_count = 0

    for sentence in sentences:
        sentence_word_count = len(
            sentence.split()
        )

        if (
            current_sentences
            and (
                current_word_count
                + sentence_word_count
                > maximum_words
            )
        ):
            chunks.append(
                " ".join(
                    current_sentences
                )
            )

            if overlap_sentences > 0:
                current_sentences = (
                    current_sentences[
                        -overlap_sentences:
                    ]
                )
            else:
                current_sentences = []

            current_word_count = sum(
                len(item.split())
                for item in current_sentences
            )

        current_sentences.append(
            sentence
        )

        current_word_count += (
            sentence_word_count
        )

    if current_sentences:
        chunks.append(
            " ".join(
                current_sentences
            )
        )

    return chunks


def normalize_embedding(
    embedding: np.ndarray,
) -> np.ndarray:
    """
    Convert an embedding to unit length.
    """

    norm = np.linalg.norm(
        embedding
    )

    if norm == 0:
        return embedding

    return embedding / norm


def calculate_cosine_score(
    first_embedding: np.ndarray,
    second_embedding: np.ndarray,
) -> float:
    """
    Calculate cosine similarity between two vectors.
    """

    first_normalized = (
        normalize_embedding(
            first_embedding
        )
    )

    second_normalized = (
        normalize_embedding(
            second_embedding
        )
    )

    score = np.dot(
        first_normalized,
        second_normalized,
    )

    return float(score)


def convert_similarity_to_percentage(
    similarity: float,
) -> float:
    """
    Convert cosine similarity into a percentage
    between 0 and 100.

    Negative values are treated as zero.
    """

    bounded_similarity = max(
        0.0,
        min(
            float(similarity),
            1.0,
        ),
    )

    return round(
        bounded_similarity * 100,
        2,
    )


def encode_texts(
    texts: list[str],
) -> np.ndarray:
    """
    Encode text values using the cached semantic model.
    """

    cleaned_texts = []
    for text in texts:
        cleaned = clean_semantic_text(text)
        if cleaned:
            cleaned_texts.append(cleaned)

    if not cleaned_texts:
        raise ValueError(
            "At least one non-empty text is required "
            "for encoding."
        )

    cache_limit = settings.semantic_result_cache_size
    keys = [_embedding_key(text) for text in cleaned_texts]

    if cache_limit > 0:
        with _cache_lock:
            cached = [_embedding_cache.get(key) for key in keys]
            if all(item is not None for item in cached):
                for key in keys:
                    _embedding_cache.move_to_end(key)
                return np.stack(cached).astype(np.float32, copy=False)

    with _inference_lock:
        if cache_limit > 0:
            with _cache_lock:
                cached = [_embedding_cache.get(key) for key in keys]
                missing_indexes = [
                    index for index, item in enumerate(cached) if item is None
                ]
        else:
            cached = [None] * len(keys)
            missing_indexes = list(range(len(keys)))

        if missing_indexes:
            model = get_semantic_model()
            encoded = np.asarray(
                model.encode(
                    [cleaned_texts[index] for index in missing_indexes],
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                ),
                dtype=np.float32,
            )
            for index, embedding in zip(missing_indexes, encoded):
                cached[index] = embedding

            if cache_limit > 0:
                with _cache_lock:
                    for index in missing_indexes:
                        key = keys[index]
                        _embedding_cache[key] = cached[index]
                        _embedding_cache.move_to_end(key)
                    while len(_embedding_cache) > cache_limit:
                        _embedding_cache.popitem(last=False)

        return np.stack(cached).astype(np.float32, copy=False)


def calculate_document_embedding(
    text: str,
) -> np.ndarray:
    """
    Create one document embedding by averaging
    its chunk embeddings.
    """

    chunks = create_text_chunks(
        text
    )

    if not chunks:
        raise ValueError(
            "Cannot create an embedding from empty text."
        )

    chunk_embeddings = encode_texts(
        chunks
    )

    document_embedding = np.mean(
        chunk_embeddings,
        axis=0,
    )

    return normalize_embedding(
        document_embedding
    )


def calculate_semantic_similarity(
    resume_text: str,
    job_description: str,
) -> float:
    """
    Calculate transformer-based semantic similarity between
    a resume and a job description.
    """

    if (
        not resume_text.strip()
        or not job_description.strip()
    ):
        return 0.0

    resume_embedding = (
        calculate_document_embedding(
            resume_text
        )
    )

    job_embedding = (
        calculate_document_embedding(
            job_description
        )
    )

    similarity = calculate_cosine_score(
        resume_embedding,
        job_embedding,
    )

    return convert_similarity_to_percentage(
        similarity
    )


def calculate_chunk_matches(
    resume_text: str,
    job_description: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Find resume chunks most similar to
    job-description chunks.

    This provides explainability by showing which
    resume content contributed most to the semantic score.
    """

    if top_k < 1:
        raise ValueError(
            "top_k must be at least 1."
        )

    resume_chunks = create_text_chunks(
        resume_text
    )

    job_chunks = create_text_chunks(
        job_description
    )

    if (
        not resume_chunks
        or not job_chunks
    ):
        return []

    resume_embeddings = encode_texts(
        resume_chunks
    )

    job_embeddings = encode_texts(
        job_chunks
    )

    results: list[dict] = []

    for (
        resume_index,
        resume_embedding,
    ) in enumerate(
        resume_embeddings
    ):
        similarities = np.dot(
            job_embeddings,
            resume_embedding,
        )

        best_job_index = int(
            np.argmax(
                similarities
            )
        )

        best_similarity = float(
            similarities[
                best_job_index
            ]
        )

        results.append(
            {
                "resume_chunk": (
                    resume_chunks[
                        resume_index
                    ]
                ),
                "job_description_chunk": (
                    job_chunks[
                        best_job_index
                    ]
                ),
                "similarity_percentage": (
                    convert_similarity_to_percentage(
                        best_similarity
                    )
                ),
            }
        )

    sorted_results = sorted(
        results,
        key=lambda item: item[
            "similarity_percentage"
        ],
        reverse=True,
    )

    return sorted_results[
        :top_k
    ]


def calculate_semantic_analysis(
    resume_text: str,
    job_description: str,
    top_k: int = 5,
) -> tuple[float, list[dict]]:
    """Calculate document similarity and chunk matches from one encoding pass."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    resume_chunks = create_text_chunks(resume_text)
    job_chunks = create_text_chunks(job_description)
    if not resume_chunks or not job_chunks:
        return 0.0, []

    resume_embeddings = encode_texts(resume_chunks)
    job_embeddings = encode_texts(job_chunks)
    resume_document = normalize_embedding(np.mean(resume_embeddings, axis=0))
    job_document = normalize_embedding(np.mean(job_embeddings, axis=0))
    score = convert_similarity_to_percentage(
        calculate_cosine_score(resume_document, job_document)
    )

    matches = []
    for resume_chunk, resume_embedding in zip(
        resume_chunks,
        resume_embeddings,
    ):
        similarities = np.dot(job_embeddings, resume_embedding)
        best_index = int(np.argmax(similarities))
        matches.append(
            {
                "resume_chunk": resume_chunk,
                "job_description_chunk": job_chunks[best_index],
                "similarity_percentage": convert_similarity_to_percentage(
                    float(similarities[best_index])
                ),
            }
        )

    matches.sort(
        key=lambda item: item["similarity_percentage"],
        reverse=True,
    )
    return score, matches[:top_k]

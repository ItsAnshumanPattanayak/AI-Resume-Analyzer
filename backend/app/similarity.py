import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def preprocess_text(text: str) -> str:
    """
    Prepare text for TF-IDF comparison.

    Keeps important technical symbols such as:
    C++, C#, .NET and CI/CD.
    """

    if not text:
        return ""

    text = text.lower()

    # Convert line breaks and tabs to spaces.
    text = text.replace("\n", " ").replace("\t", " ")

    # Keep letters, numbers and selected technical symbols.
    text = re.sub(r"[^a-z0-9+#./\-\s]", " ", text)

    # Remove repeated whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def calculate_tfidf_similarity(
    resume_text: str,
    job_description: str,
) -> float:
    """
    Calculate semantic keyword similarity using TF-IDF
    and cosine similarity.

    Returns a percentage between 0 and 100.
    """

    cleaned_resume = preprocess_text(resume_text)
    cleaned_job_description = preprocess_text(job_description)

    if not cleaned_resume or not cleaned_job_description:
        return 0.0

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000,
            sublinear_tf=True,
        )

        tfidf_matrix = vectorizer.fit_transform(
            [
                cleaned_resume,
                cleaned_job_description,
            ]
        )

        similarity = cosine_similarity(
            tfidf_matrix[0:1],
            tfidf_matrix[1:2],
        )[0][0]

        similarity_percentage = similarity * 100

        return round(float(similarity_percentage), 2)

    except ValueError:
        # This can occur when both documents contain no usable vocabulary.
        return 0.0

def calculate_combined_similarity(
    tfidf_similarity: float,
    semantic_similarity: float,
) -> dict:
    """
    Combine lexical and semantic similarity.

    Semantic similarity receives more weight because it can detect
    meaning even when the resume and job description use different
    wording.
    """

    tfidf_weight = 0.35
    semantic_weight = 0.65

    combined_score = (
        tfidf_similarity * tfidf_weight
        + semantic_similarity * semantic_weight
    )

    return {
        "combined_percentage": round(combined_score, 2),
        "tfidf_percentage": round(tfidf_similarity, 2),
        "semantic_percentage": round(
            semantic_similarity,
            2,
        ),
        "weights": {
            "tfidf": tfidf_weight,
            "semantic": semantic_weight,
        },
    }
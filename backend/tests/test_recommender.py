import pytest

from app.recommender import recommend_job_roles


pytestmark = pytest.mark.semantic


resume_text = """
ANSHUMAN PATTANAYAK

Computer Science student with experience in Python,
machine learning, deep learning and artificial intelligence.

TECHNICAL SKILLS
Python, FastAPI, SQL, Git, GitHub, Pandas, NumPy,
Scikit-learn, PyTorch, TensorFlow, Machine Learning,
Deep Learning, NLP, RAG, LangChain and MongoDB.

PROJECTS
Built an AI resume analyzer using Python, FastAPI,
TF-IDF, cosine similarity and Sentence Transformers.

Developed machine learning projects using Pandas,
Scikit-learn and data preprocessing techniques.

Created agentic AI applications using LangChain,
retrieval augmented generation and large language models.
"""


def test_recommend_job_roles() -> None:
    result = recommend_job_roles(
        resume_text=resume_text,
        top_n=5,
    )

    assert "python" in result["candidate_skills"]
    assert result["best_role"]
    assert len(result["recommended_roles"]) == 5

    match_percentages = [
        recommendation[
            "overall_match_percentage"
        ]
        for recommendation in result[
            "recommended_roles"
        ]
    ]

    assert match_percentages == sorted(
        match_percentages,
        reverse=True,
    )

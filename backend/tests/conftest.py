import io

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Create one reusable FastAPI test client.
    """

    return TestClient(app)


@pytest.fixture
def sample_resume_text() -> str:
    """
    Return a realistic resume sample for unit tests.
    """

    return """
ANSHUMAN PATTANAYAK

Email: anshuman@example.com
Phone: +91 9876543210
LinkedIn: https://linkedin.com/in/anshuman
GitHub: https://github.com/anshuman

SUMMARY
Computer Science student with practical experience developing
Python, machine learning and artificial intelligence projects.

TECHNICAL SKILLS
Python, FastAPI, SQL, Git, GitHub, Pandas, NumPy,
Scikit-learn, PyTorch, TensorFlow, Machine Learning,
Deep Learning, NLP, RAG, LangChain and MongoDB.

EDUCATION
B.Tech in Computer Science and Engineering
Centurion University of Technology and Management
CGPA: 8.2

PROJECTS
Developed an AI resume analyzer using Python, FastAPI,
TF-IDF and Sentence Transformers.

Built 15 artificial intelligence and machine learning projects.

Improved model accuracy by 18% using feature engineering.
""".strip()


@pytest.fixture
def sample_job_description() -> str:
    """
    Return a sample job description for matching tests.
    """

    return """
We are hiring a Python AI Engineer with experience in FastAPI,
machine learning, SQL, Git, Docker, AWS and REST APIs.

The candidate should understand deep learning, NLP, data
preprocessing and deployment of artificial intelligence systems.
""".strip()


@pytest.fixture
def simple_docx_bytes(sample_resume_text: str) -> bytes:
    """
    Create an in-memory DOCX resume for API upload tests.
    """

    from docx import Document

    document = Document()

    for line in sample_resume_text.splitlines():
        document.add_paragraph(line)

    file_buffer = io.BytesIO()
    document.save(file_buffer)
    file_buffer.seek(0)

    return file_buffer.read()
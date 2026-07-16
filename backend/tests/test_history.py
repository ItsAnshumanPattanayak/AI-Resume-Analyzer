from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.history import (
    create_analysis_record,
    delete_analysis_record,
    get_analysis_record,
    list_analysis_records,
)


def create_test_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
    )

    Base.metadata.create_all(engine)

    return Session(engine)


def test_create_and_get_analysis_record() -> None:
    session = create_test_session()

    result_data = {
        "candidate": {
            "name": "Anshuman Pattanayak",
        },
        "ats": {
            "overall_score": 82.5,
        },
        "resume_improvement": {
            "quality_score": 75.0,
        },
        "job_role_recommendations": {
            "best_role": {
                "role": "AI Engineer",
            },
        },
    }

    record = create_analysis_record(
        session,
        analysis_type="analyze",
        filename="resume.pdf",
        result_data=result_data,
    )

    saved = get_analysis_record(
        session,
        record.id,
    )

    assert saved is not None
    assert saved.candidate_name == (
        "Anshuman Pattanayak"
    )
    assert saved.ats_score == 82.5
    assert saved.best_role == "AI Engineer"

    session.close()


def test_list_and_delete_records() -> None:
    session = create_test_session()

    record = create_analysis_record(
        session,
        analysis_type="parse",
        filename="resume.docx",
        result_data={
            "candidate": {
                "name": "Test Candidate",
            }
        },
    )

    records = list_analysis_records(
        session
    )

    assert len(records) == 1

    delete_analysis_record(
        session,
        record,
    )

    assert get_analysis_record(
        session,
        record.id,
    ) is None

    session.close()
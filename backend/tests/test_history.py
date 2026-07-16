from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.history import (
    create_analysis_record,
    delete_analysis_record,
    get_analysis_record,
    list_analysis_records,
)
from app.models import User


def create_test_session() -> Session:
    """
    Create an isolated in-memory database.
    """

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
    )

    Base.metadata.create_all(engine)

    return Session(engine)


def create_test_user(
    session: Session,
    *,
    name: str = "History Test User",
    email: str = "history@example.com",
) -> User:
    """
    Create a user for history ownership tests.
    """

    user = User(
        name=name,
        email=email,
        password_hash="test-password-hash",
        is_active=True,
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def test_create_and_get_analysis_record() -> None:
    session = create_test_session()

    try:
        user = create_test_user(session)

        result_data = {
            "candidate": {
                "name": (
                    "Anshuman Pattanayak"
                ),
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
            user_id=user.id,
            analysis_type="analyze",
            filename="resume.pdf",
            result_data=result_data,
        )

        saved = get_analysis_record(
            session,
            record_id=record.id,
            user_id=user.id,
        )

        assert saved is not None
        assert saved.user_id == user.id
        assert saved.candidate_name == (
            "Anshuman Pattanayak"
        )
        assert saved.ats_score == 82.5
        assert saved.quality_score == 75.0
        assert saved.best_role == (
            "AI Engineer"
        )

    finally:
        session.close()


def test_list_and_delete_records() -> None:
    session = create_test_session()

    try:
        user = create_test_user(session)

        record = create_analysis_record(
            session,
            user_id=user.id,
            analysis_type="parse",
            filename="resume.docx",
            result_data={
                "parsed_data": {
                    "name": (
                        "Test Candidate"
                    ),
                }
            },
        )

        record_id = record.id

        records = list_analysis_records(
            session,
            user_id=user.id,
        )

        assert len(records) == 1
        assert records[0].id == record_id
        assert records[0].user_id == user.id

        delete_analysis_record(
            session,
            record,
        )

        deleted_record = (
            get_analysis_record(
                session,
                record_id=record_id,
                user_id=user.id,
            )
        )

        assert deleted_record is None

    finally:
        session.close()


def test_users_cannot_read_each_others_records() -> None:
    session = create_test_session()

    try:
        first_user = create_test_user(
            session,
            name="First User",
            email="first-history@example.com",
        )

        second_user = create_test_user(
            session,
            name="Second User",
            email="second-history@example.com",
        )

        record = create_analysis_record(
            session,
            user_id=first_user.id,
            analysis_type="improve",
            filename="private-resume.pdf",
            result_data={
                "success": True,
                "candidate": {
                    "name": "Private Candidate",
                },
            },
        )

        owner_result = get_analysis_record(
            session,
            record_id=record.id,
            user_id=first_user.id,
        )

        other_user_result = (
            get_analysis_record(
                session,
                record_id=record.id,
                user_id=second_user.id,
            )
        )

        assert owner_result is not None
        assert other_user_result is None

        first_user_records = (
            list_analysis_records(
                session,
                user_id=first_user.id,
            )
        )

        second_user_records = (
            list_analysis_records(
                session,
                user_id=second_user.id,
            )
        )

        assert len(first_user_records) == 1
        assert second_user_records == []

    finally:
        session.close()
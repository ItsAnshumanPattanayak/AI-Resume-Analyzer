from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import AnalysisRecord


def extract_history_summary(
    analysis_type: str,
    result_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Extract summary fields from a complete analysis result.
    """

    candidate = result_data.get(
        "candidate",
        {},
    )

    if not candidate:
        candidate = result_data.get(
            "parsed_data",
            {},
        )

    candidate_name = candidate.get(
        "name"
    )

    ats_score = (
        result_data.get("ats", {})
        .get("overall_score")
    )

    improvement = result_data.get(
        "resume_improvement",
        {},
    )

    quality_score = improvement.get(
        "quality_score"
    )

    role_container = result_data.get(
        "job_role_recommendations"
    )

    if role_container is None:
        role_container = result_data.get(
            "recommendations",
            {},
        )

    best_role = None

    if isinstance(role_container, dict):
        best_role_data = role_container.get(
            "best_role"
        )

        if isinstance(best_role_data, dict):
            best_role = best_role_data.get(
                "role"
            )

        elif isinstance(
            best_role_data,
            str,
        ):
            best_role = best_role_data

        if best_role is None:
            recommended_roles = (
                role_container.get(
                    "recommended_roles",
                    [],
                )
            )

            if recommended_roles:
                first_role = recommended_roles[0]

                if isinstance(first_role, dict):
                    best_role = first_role.get(
                        "role"
                    )

    return {
        "analysis_type": analysis_type,
        "candidate_name": candidate_name,
        "ats_score": ats_score,
        "quality_score": quality_score,
        "best_role": best_role,
    }


def create_analysis_record(
    database_session: Session,
    *,
    user_id: int,
    analysis_type: str,
    filename: str,
    result_data: dict[str, Any],
) -> AnalysisRecord:
    """
    Save one analysis result for a specific user.
    """

    summary = extract_history_summary(
        analysis_type=analysis_type,
        result_data=result_data,
    )

    record = AnalysisRecord(
        user_id=user_id,
        analysis_type=analysis_type,
        filename=filename,
        candidate_name=summary[
            "candidate_name"
        ],
        ats_score=summary[
            "ats_score"
        ],
        quality_score=summary[
            "quality_score"
        ],
        best_role=summary[
            "best_role"
        ],
        result_data=result_data,
    )

    database_session.add(record)
    database_session.commit()
    database_session.refresh(record)

    return record


def list_analysis_records(
    database_session: Session,
    *,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> list[AnalysisRecord]:
    """
    Return reports belonging only to one user.
    """

    statement = (
        select(AnalysisRecord)
        .where(
            AnalysisRecord.user_id
            == user_id
        )
        .order_by(
            desc(
                AnalysisRecord.created_at
            )
        )
        .offset(offset)
        .limit(limit)
    )

    return list(
        database_session.scalars(
            statement
        ).all()
    )


def get_analysis_record(
    database_session: Session,
    *,
    record_id: int,
    user_id: int,
) -> AnalysisRecord | None:
    """
    Find one record belonging to a user.
    """

    statement = select(
        AnalysisRecord
    ).where(
        AnalysisRecord.id == record_id,
        AnalysisRecord.user_id
        == user_id,
    )

    return database_session.scalar(
        statement
    )


def delete_analysis_record(
    database_session: Session,
    record: AnalysisRecord,
) -> None:
    """
    Delete one saved analysis record.
    """

    database_session.delete(record)
    database_session.commit()
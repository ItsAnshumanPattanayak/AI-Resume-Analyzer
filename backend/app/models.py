from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnalysisRecord(Base):
    """
    Store one completed resume analysis report.
    """

    __tablename__ = "analysis_records"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    analysis_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    candidate_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ats_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    quality_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    best_role: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    result_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
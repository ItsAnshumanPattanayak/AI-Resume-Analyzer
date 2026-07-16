from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AnalysisHistoryItem(BaseModel):
    """
    Small summary used in the history list.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    analysis_type: str
    filename: str
    candidate_name: str | None
    ats_score: float | None
    quality_score: float | None
    best_role: str | None
    created_at: datetime


class AnalysisHistoryDetail(
    AnalysisHistoryItem
):
    """
    Full saved analysis report.
    """

    result_data: dict[str, Any]


class DeleteHistoryResponse(BaseModel):
    success: bool
    deleted_id: int
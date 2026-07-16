from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


class UserRegisterRequest(BaseModel):
    """
    Data required to create an account.
    """

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserLoginRequest(BaseModel):
    """
    Login credentials submitted by the frontend.
    """

    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=128,
    )


class UserResponse(BaseModel):
    """
    Public user information.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime


class AccessTokenResponse(BaseModel):
    """
    JWT response returned after login.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


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
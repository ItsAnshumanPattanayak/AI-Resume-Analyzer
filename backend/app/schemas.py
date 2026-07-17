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


class RecommendationScoreComponent(BaseModel):
    """One weighted component of a role recommendation score."""

    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    weighted_score: float = Field(ge=0, le=100)


class RecommendationFinalScore(BaseModel):
    """Final score used to order recommendations."""

    score: float = Field(ge=0, le=100)


class RecommendationScoreComponents(BaseModel):
    """Transparent values used to calculate one recommendation."""

    exact_skill_coverage: RecommendationScoreComponent
    semantic_similarity: RecommendationScoreComponent
    final_score: RecommendationFinalScore


class RoleRecommendationItem(BaseModel):
    """One explainable, ranked recommendation for a predefined role."""

    role: str
    overall_match_percentage: float = Field(ge=0, le=100)
    recommendation_level: str
    skill_match_percentage: float = Field(ge=0, le=100)
    exact_skill_match_percentage: float = Field(ge=0, le=100)
    semantic_match_percentage: float = Field(ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    candidate_relevant_skills: list[str]
    total_required_skills: int = Field(ge=0)
    matched_skill_count: int = Field(ge=0)
    missing_skill_count: int = Field(ge=0)
    strengths: list[str]
    improvement_areas: list[str]
    explanation: str
    score_components: RecommendationScoreComponents
    role_description: str
    reason: str


class RecommendationScoringWeights(BaseModel):
    """Weights shared by all role recommendations in a response."""

    skills: float = Field(ge=0, le=1)
    semantic_similarity: float = Field(ge=0, le=1)


class RoleRecommendationsPayload(BaseModel):
    """Recommendation data calculated from an uploaded resume."""

    candidate_skills: list[str]
    total_candidate_skills: int = Field(ge=0)
    scoring_weights: RecommendationScoringWeights
    best_role: RoleRecommendationItem | None
    recommended_roles: list[RoleRecommendationItem]
    roles_evaluated: int = Field(ge=0)


class RoleRecommendationCandidate(BaseModel):
    """Candidate fields returned by the role-recommendation endpoint."""

    name: str | None
    email: str | None
    phone: str | None
    links: dict[str, str | None]
    skills: dict[str, Any]


class RoleRecommendationResponse(BaseModel):
    """Documented response for the authenticated role endpoint."""

    success: bool
    filename: str
    content_type: str | None
    file_size_bytes: int = Field(ge=0)
    resume_statistics: dict[str, int]
    candidate: RoleRecommendationCandidate
    recommendations: RoleRecommendationsPayload
    history_id: int = Field(ge=1)

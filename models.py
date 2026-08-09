from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, List, Optional


class CandidateInput(BaseModel):
    social_profile: Dict[str, Any]
    interaction_profile: Dict[str, Any]


class CandidateRequest(BaseModel):
    first_name: str = Field(max_length=80)
    last_name: str = Field(max_length=80)
    email: str = Field(default="", max_length=254)
    phone: str = Field(default="", max_length=30)

    @field_validator("first_name", "last_name")
    @classmethod
    def require_non_empty_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name fields cannot be empty.")
        return normalized

    @field_validator("email", "phone")
    @classmethod
    def normalize_optional_fields(cls, value: str) -> str:
        return value.strip()


class DashboardView(BaseModel):
    full_name: str
    email: str
    phone: str
    match_percent: float
    status: str


class InterviewGraph(BaseModel):
    communication: float
    confidence: float
    reliability: float
    role_fit: float
    motivation: float
    availability: float
    stability: float
    customer_orientation: float
    clarity: float
    engagement: float


class InterviewDetails(BaseModel):
    graph: InterviewGraph
    strengths: List[str]
    weaker_points: List[str]
    score_reasons: List[str]


class AgentOutput(BaseModel):
    dashboard_view: DashboardView
    interview_details: InterviewDetails

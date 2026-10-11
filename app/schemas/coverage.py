from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class CoverageJobInput(BaseModel):
    pass


class CoverageAlertView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    activity_id: str
    student_member_id: str
    category: str
    status: str
    input_roster_version: int
    need_summary: Optional[str] = None
    missing_tags: Optional[list[str]] = None
    analyzed_expert_ids: Optional[list[str]] = None
    evidence: Optional[str] = None
    reviews: list[dict] = []


class CoverageReviewInput(BaseModel):
    conclusion: str = Field(pattern="^(NEEDS_MORE_INFO|EXISTING_SUPPORT_CONFIRMED|NEEDS_OUTREACH|RESOLVED)$")
    reason: Optional[str] = None
    expected_version: int

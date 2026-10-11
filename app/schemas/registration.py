from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from app.schemas.common import SubmissionStatus, ReviewStatus, ParticipationStatus


class JoinInput(BaseModel):
    role: str = Field(pattern="^(STUDENT|EXPERT)$")


class BasicInfo(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    branch: Optional[str] = None
    branch_other: Optional[str] = None
    identity: Optional[str] = None
    project: Optional[str] = None
    industries: Optional[list[str]] = None


class DraftPatch(BaseModel):
    basic: Optional[BasicInfo] = None
    sections: Optional[dict] = None
    structured: Optional[dict] = None


class SubmitInput(BaseModel):
    confirmed: bool = True


class HistoryCopyInput(BaseModel):
    source_snapshot_id: str


class ReasonInput(BaseModel):
    reason: str = Field(min_length=1)


class SnapshotView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    snapshot_id: str
    activity_id: str
    submitted_at: str
    submission_source: str
    content: dict
    public_dossier: Optional[dict] = None


class RegistrationView(BaseModel):
    activity_id: str
    activity_member_id: str
    role: str
    submission_status: SubmissionStatus
    review_status: ReviewStatus
    participation_status: ParticipationStatus
    capacity_max: int
    server_time: str
    draft: Optional[dict] = None
    current_snapshot: Optional[SnapshotView] = None
    review_decision: Optional[dict] = None
    public_preview: Optional[dict] = None
    privacy_warnings: Optional[list[str]] = None

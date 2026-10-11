from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from app.schemas.common import ActivityStatus


class ActivityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None


class ActivityPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    registration_starts_at: Optional[str] = None
    registration_deadline: Optional[str] = None
    student_choice_starts_at: Optional[str] = None
    student_choice_deadline: Optional[str] = None
    expert_selection_starts_at: Optional[str] = None
    expert_response_deadline: Optional[str] = None
    supplement_choice_starts_at: Optional[str] = None
    supplement_choice_deadline: Optional[str] = None
    max_choices_per_student: Optional[int] = Field(default=None, ge=1)
    capacity_max: Optional[int] = Field(default=None, ge=1)
    reason: str = Field(min_length=1)
    expected_version: int


class VersionInput(BaseModel):
    expected_version: int


class ActivitySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    activity_id: str
    name: str
    status: ActivityStatus
    registration_starts_at: Optional[str] = None
    registration_deadline: Optional[str] = None
    version: int


class PublicActivitySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    activity_id: str
    name: str
    description: Optional[str] = None
    registration_starts_at: Optional[str] = None
    registration_deadline: Optional[str] = None


class ActivityView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    activity_id: str
    name: str
    description: Optional[str] = None
    status: ActivityStatus
    registration_starts_at: Optional[str] = None
    registration_deadline: Optional[str] = None
    student_choice_starts_at: Optional[str] = None
    student_choice_deadline: Optional[str] = None
    expert_selection_starts_at: Optional[str] = None
    expert_response_deadline: Optional[str] = None
    supplement_choice_starts_at: Optional[str] = None
    supplement_choice_deadline: Optional[str] = None
    max_choices_per_student: int
    capacity_max: int
    version: int

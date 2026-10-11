from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class ManualExpertInput(BaseModel):
    user_id: Optional[str] = None
    name: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    wechat: Optional[str] = None
    branch: str = Field(min_length=1)
    branch_other: Optional[str] = None
    identity: Optional[str] = None
    project: Optional[str] = None
    industries: Optional[list[str]] = None
    topics: Optional[list[str]] = None


class ManualDraftPatch(BaseModel):
    basic: Optional[dict] = None
    sections: Optional[dict] = None
    structured: Optional[dict] = None


class ManualSubmitInput(BaseModel):
    confirmation_basis: str = Field(min_length=1)
    expected_version: int = Field(ge=1)


class CapacityUpdateInput(BaseModel):
    capacity_override: Optional[int] = Field(ge=0)
    reason: str = Field(min_length=1)
    expected_version: int = Field(ge=1)


class CapacityUpdateView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    activity_member_id: str
    capacity_override: Optional[int] = None
    effective_capacity: int
    version: int


class MemberParticipationChanged(BaseModel):
    activity_id: str
    activity_member_id: str
    role: str
    previous_status: str
    participation_status: str
    reason: Optional[str] = None
    changed_at: str

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class ReviewInput(BaseModel):
    decision: str = Field(pattern="^(APPROVED|REJECTED)$")
    reason: Optional[str] = None
    expected_version: int
    privacy_reviewed: bool = True


class ContactPatch(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    reason: str = Field(min_length=1)
    expected_version: int


class NoteInput(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class NoteView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    content: str
    author_id: str
    created_at: str


class AdminSubmitInput(BaseModel):
    confirmation_basis: str = Field(min_length=1)
    expected_version: int


class ManualRegistrationInput(BaseModel):
    user_id: Optional[str] = None
    role: str = Field(pattern="^(STUDENT|EXPERT)$")
    name: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    wechat: Optional[str] = None


class ContactView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    activity_member_id: str
    name: str
    phone: str
    wechat: Optional[str] = None
    version: int


class AdminRegistrationView(BaseModel):
    activity_id: str
    activity_member_id: str
    user_id: str
    role: str
    submission_status: str
    review_status: str
    participation_status: str
    version: int
    contact: Optional[ContactView] = None
    draft: Optional[dict] = None
    current_snapshot: Optional[dict] = None
    review_decisions: list[dict] = []
    notes: list[NoteView] = []
    public_preview: Optional[dict] = None


class RegistrationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    activity_member_id: str
    user_id: str
    role: str
    display_name: str
    submission_status: str
    review_status: str
    participation_status: str
    branch: Optional[str] = None

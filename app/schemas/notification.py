from pydantic import BaseModel, Field
from typing import Optional


class NotificationView(BaseModel):
    id: str
    activity_id: Optional[str] = None
    notification_type: str
    title: str
    body: Optional[str] = None
    target_id: Optional[str] = None
    is_read: bool
    read_at: Optional[str] = None
    created_at: str


class ReminderInput(BaseModel):
    member_ids: list[str] = Field(min_length=1, max_length=100)
    template: str = Field(min_length=1)


class ReminderResult(BaseModel):
    created: int
    deduplicated: int
    rejected: int
    rejection_reasons: list[str] = []

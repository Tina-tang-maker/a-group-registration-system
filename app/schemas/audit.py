from pydantic import BaseModel
from typing import Optional


class AuditView(BaseModel):
    id: str
    activity_id: Optional[str] = None
    actor_user_id: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    detail: Optional[dict] = None
    created_at: str


class DashboardView(BaseModel):
    activity_id: str
    total_members: int
    total_students: int
    total_experts: int
    submitted: int
    pending_review: int
    approved: int
    rejected: int
    active: int
    withdrawn: int
    inactive: int
    expert_capacity_total: int

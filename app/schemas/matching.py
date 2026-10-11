from pydantic import BaseModel
from typing import Optional


class MemberView(BaseModel):
    activity_id: str
    activity_member_id: str
    role: str
    review_status: str
    display_name: str


class ExpertSections(BaseModel):
    experience: str
    supported_problems: str
    boundaries: str


class EligibleExpert(BaseModel):
    activity_id: str
    activity_member_id: str
    expert_profile_id: Optional[str] = None
    expertise: list[str]
    available: bool = True
    profile_summary: str
    subtitle: str
    sections: ExpertSections


class StudentSections(BaseModel):
    background: str
    problem: str
    expected_help: str


class StudentNeed(BaseModel):
    activity_id: str
    activity_member_id: str
    title: str
    summary: str
    preferred_topics: list[str]
    sections: StudentSections


class ActivityRules(BaseModel):
    activity_id: str
    name: str
    status: str
    student_choice_starts_at: Optional[str] = None
    student_choice_deadline: Optional[str] = None
    expert_selection_starts_at: Optional[str] = None
    expert_response_deadline: Optional[str] = None
    supplement_choice_starts_at: Optional[str] = None
    supplement_choice_deadline: Optional[str] = None
    max_choices_per_student: int
    capacity_max: int


class MatchingInputResponse(BaseModel):
    activity: ActivityRules
    members: list[MemberView]
    eligible_experts: list[EligibleExpert]
    student_needs: list[StudentNeed]

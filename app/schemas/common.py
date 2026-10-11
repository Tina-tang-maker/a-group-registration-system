from pydantic import BaseModel, Field
from typing import TypeVar, Generic, Sequence
from enum import Enum


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    page_size: int


class PageQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class DeletedResult(BaseModel):
    deleted: bool = True


class ActivityStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"


class MemberRole(str, Enum):
    STUDENT = "STUDENT"
    EXPERT = "EXPERT"
    OPERATOR = "OPERATOR"


class SubmissionStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"


class ReviewStatus(str, Enum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ParticipationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WITHDRAWN = "WITHDRAWN"
    INACTIVE = "INACTIVE"


class ReviewDecisionEnum(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class CoverageCategory(str, Enum):
    INFORMATION_INSUFFICIENT = "INFORMATION_INSUFFICIENT"
    POSSIBLE_EXPERT_GAP = "POSSIBLE_EXPERT_GAP"
    CAPACITY_PRESSURE = "CAPACITY_PRESSURE"


class CoverageConclusion(str, Enum):
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
    EXISTING_SUPPORT_CONFIRMED = "EXISTING_SUPPORT_CONFIRMED"
    NEEDS_OUTREACH = "NEEDS_OUTREACH"
    RESOLVED = "RESOLVED"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class JobType(str, Enum):
    REPLY = "REPLY"
    DOSSIER = "DOSSIER"
    COVERAGE = "COVERAGE"

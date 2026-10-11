from app.database import Base, TimestampMixin, generate_uuid
from sqlalchemy import String, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column


class CoverageAlert(Base, TimestampMixin):
    __tablename__ = "coverage_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    activity_id: Mapped[str] = mapped_column(String(36), ForeignKey("activities.id"), nullable=False)
    student_member_id: Mapped[str] = mapped_column(String(36), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)

    input_roster_version: Mapped[int] = mapped_column(Integer, nullable=False)
    need_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    missing_tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    analyzed_expert_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)

    supersedes_alert_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class CoverageReview(Base, TimestampMixin):
    __tablename__ = "coverage_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    alert_id: Mapped[str] = mapped_column(String(36), ForeignKey("coverage_alerts.id"), nullable=False)
    conclusion: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    input_version: Mapped[int] = mapped_column(Integer, nullable=False)

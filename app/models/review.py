from app.database import Base, TimestampMixin, generate_uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class ReviewDecision(Base, TimestampMixin):
    __tablename__ = "review_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    snapshot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("registration_snapshots.id"), nullable=False
    )
    activity_member_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("activity_members.id"), nullable=False
    )
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    decided_at: Mapped[str] = mapped_column(String(40), nullable=False)

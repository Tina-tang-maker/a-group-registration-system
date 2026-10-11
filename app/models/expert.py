from app.database import Base, TimestampMixin, generate_uuid
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class ExpertProfile(Base, TimestampMixin):
    __tablename__ = "expert_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    latest_confirmed_snapshot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class ExpertParticipation(Base, TimestampMixin):
    __tablename__ = "expert_participations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    activity_member_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("activity_members.id"), unique=True, nullable=False
    )
    approved_snapshot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    capacity_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

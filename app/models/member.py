from app.database import Base, TimestampMixin, VersionMixin, generate_uuid
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class ActivityMember(Base, TimestampMixin, VersionMixin):
    __tablename__ = "activity_members"
    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", "role", name="uq_activity_user_role"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    activity_id: Mapped[str] = mapped_column(String(36), ForeignKey("activities.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    public_display_name: Mapped[str] = mapped_column(String(50), nullable=False)
    submission_status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)
    review_status: Mapped[str] = mapped_column(String(20), default="NOT_SUBMITTED", nullable=False)
    participation_status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)

    current_submission_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    approved_snapshot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class MemberContact(Base, TimestampMixin, VersionMixin):
    __tablename__ = "member_contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    activity_member_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("activity_members.id"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    wechat: Mapped[str | None] = mapped_column(String(50), nullable=True)

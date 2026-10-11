from app.database import Base, TimestampMixin, generate_uuid
from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column


class RegistrationDraft(Base, TimestampMixin):
    __tablename__ = "registration_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    activity_member_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("activity_members.id"), unique=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    basic: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sections: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    structured: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class RegistrationSnapshot(Base, TimestampMixin):
    __tablename__ = "registration_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    activity_id: Mapped[str] = mapped_column(String(36), ForeignKey("activities.id"), nullable=False)
    activity_member_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("activity_members.id"), nullable=False
    )
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    public_dossier: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    submitted_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    submission_source: Mapped[str] = mapped_column(String(20), default="SELF", nullable=False)
    submitted_at: Mapped[str] = mapped_column(String(40), nullable=False)
    confirmation_basis: Mapped[str | None] = mapped_column(Text, nullable=True)

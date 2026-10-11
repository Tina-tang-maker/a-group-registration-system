from app.database import Base, TimestampMixin, VersionMixin, generate_uuid
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column


class Activity(Base, TimestampMixin, VersionMixin):
    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)

    registration_starts_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    registration_deadline: Mapped[str | None] = mapped_column(String(40), nullable=True)
    student_choice_starts_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    student_choice_deadline: Mapped[str | None] = mapped_column(String(40), nullable=True)
    expert_selection_starts_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    expert_response_deadline: Mapped[str | None] = mapped_column(String(40), nullable=True)
    supplement_choice_starts_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    supplement_choice_deadline: Mapped[str | None] = mapped_column(String(40), nullable=True)

    max_choices_per_student: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    capacity_max: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

from app.database import Base, TimestampMixin, generate_uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class OperatorNote(Base, TimestampMixin):
    __tablename__ = "operator_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    activity_id: Mapped[str] = mapped_column(String(36), ForeignKey("activities.id"), nullable=False)
    activity_member_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("activity_members.id"), nullable=False
    )
    author_id: Mapped[str] = mapped_column(String(36), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class IdempotencyRecord(Base, TimestampMixin):
    __tablename__ = "idempotency_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    result_data: Mapped[dict | None] = mapped_column(Text, nullable=True)
    status_code: Mapped[int] = mapped_column(default=200, nullable=False)

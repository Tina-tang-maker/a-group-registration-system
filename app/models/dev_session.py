from app.database import Base, TimestampMixin, generate_uuid
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class DevSession(Base, TimestampMixin):
    __tablename__ = "dev_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    activity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expires_at: Mapped[str] = mapped_column(String(40), nullable=False)

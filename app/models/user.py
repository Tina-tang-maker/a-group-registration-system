from app.database import Base, TimestampMixin, VersionMixin, generate_uuid
from sqlalchemy import String, Boolean, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    wechat: Mapped[str | None] = mapped_column(String(50), nullable=True)
    stable_number: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    is_placeholder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

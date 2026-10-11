from app.database import Base, TimestampMixin, generate_uuid
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class RoleGrant(Base, TimestampMixin):
    __tablename__ = "role_grants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    activity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("activities.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVITY")

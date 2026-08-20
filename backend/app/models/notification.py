"""
Notifications — system-wide feed, read/unread state, per Section 7's
"Notifications panel" screen.

`related_entity_type` + `related_entity_id` is a lightweight polymorphic
reference (not a real FK, since it can point to exams, results,
invoices, or schedules) — used so the frontend notification click-through
can deep-link to the right screen/record. We deliberately don't enforce
this with a DB constraint (a generic FK to 4 different tables isn't
expressible in SQL) — the API layer validates entity_type against a
fixed set of allowed values.
"""
from datetime import datetime

from sqlalchemy import String, Boolean, Text, ForeignKey, Index, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UniversityScopedMixin
from app.models.enums import NotificationType


class Notification(UniversityScopedMixin, TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "is_read", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType, name="notification_type"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    related_entity_type: Mapped[str | None] = mapped_column(String(50))  # "exam" | "result" | "invoice" | "schedule"
    related_entity_id: Mapped[int | None] = mapped_column()

    user: Mapped["User"] = relationship()

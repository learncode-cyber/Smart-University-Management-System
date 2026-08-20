"""
Notifications service layer — flagged addition (see api/v1/notifications.py
module docstring): Section 6 of the proposal never defined this module,
even though Sections 3 and 7 both require a working notifications feed.
"""
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.notification import Notification


def _not_found() -> AppError:
    return AppError(404, "NOT_FOUND", "Notification not found.")


def list_my_notifications(db: Session, user_id: int, unread_only: bool = False, limit: int = 50) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
    return list(db.scalars(stmt))


def get_unread_count(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id, Notification.is_read.is_(False)
        )
    ) or 0


def mark_read(db: Session, user_id: int, notification_id: int) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        raise _not_found()
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user_id: int) -> int:
    stmt = select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
    unread = list(db.scalars(stmt))
    for n in unread:
        n.is_read = True
    db.commit()
    return len(unread)

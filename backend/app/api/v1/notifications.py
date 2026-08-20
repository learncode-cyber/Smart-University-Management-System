"""
Notifications router — /api/v1/notifications/*

FLAGGED MODULE: not defined anywhere in the proposal's Section 6 API
spec, even though Section 3 ("Notifications Student Receive real-time
alerts...") and Section 7 ("Notifications panel — system-wide
notification feed with read/unread state") both require it, and several
other modules (Part 5 attendance, Part 7 fees) already create
`Notification` rows that would otherwise be permanently unreadable.
Built as a standard "my notifications" feed, available to every role.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/me", response_model=list[NotificationResponse], summary="Get own notification feed")
def list_my_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return notification_service.list_my_notifications(db, current_user.id, unread_only)


@router.get("/me/unread-count", response_model=UnreadCountResponse, summary="Get unread notification count")
def get_unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return UnreadCountResponse(unread_count=notification_service.get_unread_count(db, current_user.id))


@router.put("/{notification_id}/read", response_model=NotificationResponse, summary="Mark one notification as read")
def mark_read(
    notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return notification_service.mark_read(db, current_user.id, notification_id)


@router.post("/read-all", response_model=MessageResponse, summary="Mark all notifications as read")
def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    count = notification_service.mark_all_read(db, current_user.id)
    return MessageResponse(message=f"Marked {count} notification(s) as read.")

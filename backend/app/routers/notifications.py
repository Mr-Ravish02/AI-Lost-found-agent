import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.item import Notification
from app.schemas.admin import NotificationOut
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


def create_user_notification(
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    link: str = None,
    db: Session = None
) -> Optional[Notification]:
    """Helper to persist database notifications for users."""
    if not db or not user_id:
        return None
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            link=link,
            is_read=False
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif
    except Exception as exc:
        logger.error(f"Error creating notification: {exc}")
        return None


@router.get("", response_model=List[NotificationOut])
def get_user_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves notifications for the currently logged in user."""
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .limit(50)
        .all()
    )
    return notifications


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marks a specific notification as read."""
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.post("/mark-all-read")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marks all notifications for current user as read."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read."}

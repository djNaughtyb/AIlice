"""Notifications endpoints."""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from api.auth import get_current_user
from api.models import User, Notification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notify", tags=["notifications"])


class NotificationCreate(BaseModel):
    """Request body for sending a notification."""
    title: str
    message: str
    notification_type: str = "info"  # info, warning, error, success
    action_url: Optional[str] = None
    metadata: Optional[dict] = None


class NotificationResponse(BaseModel):
    """Response for notification details."""
    id: int
    title: str
    message: str
    notification_type: str
    read: bool
    action_url: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: str
    read_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification(
    notification_data: NotificationCreate,
    user_id: Optional[int] = Query(None, description="Target user ID (admin only)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a notification to a user.
    
    Args:
        notification_data: Notification data
        user_id: Target user ID (if not specified, sends to current user)
    """
    target_user_id = user_id if user_id else current_user.id
    
    # Check if user has permission to send to other users
    if user_id and user_id != current_user.id:
        # Only admins can send notifications to other users
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can send notifications to other users"
            )
    
    try:
        notification = Notification(
            user_id=target_user_id,
            title=notification_data.title,
            message=notification_data.message,
            notification_type=notification_data.notification_type,
            action_url=notification_data.action_url,
            metadata=notification_data.metadata
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        logger.info(f"Sent notification {notification.id} to user {target_user_id}")
        
        return NotificationResponse(
            id=notification.id,
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            read=notification.read,
            action_url=notification.action_url,
            metadata=notification.metadata,
            created_at=notification.created_at.isoformat(),
            read_at=notification.read_at.isoformat() if notification.read_at else None
        )
    except Exception as e:
        logger.error(f"Error sending notification: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )


@router.get("/history", response_model=List[NotificationResponse])
async def get_notification_history(
    unread_only: bool = Query(False, description="Return only unread notifications"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notification history for the current user.
    
    Args:
        unread_only: If True, return only unread notifications
        skip: Number of records to skip
        limit: Maximum number of records to return
    """
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.read == False)
    
    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        NotificationResponse(
            id=notif.id,
            title=notif.title,
            message=notif.message,
            notification_type=notif.notification_type,
            read=notif.read,
            action_url=notif.action_url,
            metadata=notif.metadata,
            created_at=notif.created_at.isoformat(),
            read_at=notif.read_at.isoformat() if notif.read_at else None
        )
        for notif in notifications
    ]


@router.post("/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Notification marked as read"}


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for the current user."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read == False
    ).update({
        Notification.read: True,
        Notification.read_at: datetime.utcnow()
    })
    db.commit()
    
    return {"message": "All notifications marked as read"}

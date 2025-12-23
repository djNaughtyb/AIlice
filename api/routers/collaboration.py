"""Collaboration endpoints for chat and sharing."""
import os
import logging
import uuid
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from api.auth import get_current_user
from api.models import User, ChatMessage, SharedResource

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["collaboration"])


class ChatMessageCreate(BaseModel):
    """Request body for sending a chat message."""
    room_id: str
    message: str
    message_type: str = "text"
    metadata: Optional[dict] = None


class ChatMessageResponse(BaseModel):
    """Response for chat message."""
    id: int
    room_id: str
    user_id: int
    username: str
    message: str
    message_type: str
    metadata: Optional[dict] = None
    created_at: str
    edited_at: Optional[str] = None

    class Config:
        from_attributes = True


class ShareRequest(BaseModel):
    """Request body for sharing a resource."""
    resource_type: str  # item, file, media, chat_room
    resource_id: int
    shared_with_user_id: Optional[int] = None  # None for public sharing
    permission: str = "view"  # view, edit, admin
    expires_in_days: Optional[int] = None


class ShareResponse(BaseModel):
    """Response for sharing."""
    id: int
    resource_type: str
    resource_id: int
    permission: str
    share_token: Optional[str] = None
    share_url: Optional[str] = None
    expires_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/chat/send", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a chat message to a room.
    
    Args:
        message_data: Chat message data
    """
    try:
        chat_message = ChatMessage(
            room_id=message_data.room_id,
            user_id=current_user.id,
            message=message_data.message,
            message_type=message_data.message_type,
            metadata=message_data.metadata
        )
        
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        
        logger.info(f"Sent chat message {chat_message.id} in room {message_data.room_id}")
        
        return ChatMessageResponse(
            id=chat_message.id,
            room_id=chat_message.room_id,
            user_id=chat_message.user_id,
            username=current_user.username,
            message=chat_message.message,
            message_type=chat_message.message_type,
            metadata=chat_message.metadata,
            created_at=chat_message.created_at.isoformat(),
            edited_at=chat_message.edited_at.isoformat() if chat_message.edited_at else None
        )
    except Exception as e:
        logger.error(f"Error sending chat message: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send chat message: {str(e)}"
        )


@router.get("/chat/{room_id}", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    room_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get chat messages from a room.
    
    Args:
        room_id: Chat room ID
        skip: Number of messages to skip
        limit: Maximum number of messages to return
    """
    messages = db.query(ChatMessage).filter(
        ChatMessage.room_id == room_id,
        ChatMessage.deleted == False
    ).order_by(ChatMessage.created_at.desc()).offset(skip).limit(limit).all()
    
    # Get user info for each message
    result = []
    for msg in messages:
        user = db.query(User).filter(User.id == msg.user_id).first()
        result.append(ChatMessageResponse(
            id=msg.id,
            room_id=msg.room_id,
            user_id=msg.user_id,
            username=user.username if user else "Unknown",
            message=msg.message,
            message_type=msg.message_type,
            metadata=msg.metadata,
            created_at=msg.created_at.isoformat(),
            edited_at=msg.edited_at.isoformat() if msg.edited_at else None
        ))
    
    return result


@router.post("/collab/share", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
async def share_resource(
    share_data: ShareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Share a resource with another user or publicly.
    
    Args:
        share_data: Sharing configuration
    """
    try:
        # Generate share token for public sharing
        share_token = None
        if not share_data.shared_with_user_id:
            share_token = str(uuid.uuid4())
        
        # Calculate expiration
        expires_at = None
        if share_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=share_data.expires_in_days)
        
        shared_resource = SharedResource(
            resource_type=share_data.resource_type,
            resource_id=share_data.resource_id,
            owner_id=current_user.id,
            shared_with_user_id=share_data.shared_with_user_id,
            permission=share_data.permission,
            share_token=share_token,
            expires_at=expires_at
        )
        
        db.add(shared_resource)
        db.commit()
        db.refresh(shared_resource)
        
        logger.info(f"Shared resource {share_data.resource_type}:{share_data.resource_id}")
        
        # Generate share URL for public shares
        share_url = None
        if share_token:
            base_url = os.getenv("BASE_URL", "http://localhost:8080")
            share_url = f"{base_url}/shared/{share_token}"
        
        return ShareResponse(
            id=shared_resource.id,
            resource_type=shared_resource.resource_type,
            resource_id=shared_resource.resource_id,
            permission=shared_resource.permission,
            share_token=shared_resource.share_token,
            share_url=share_url,
            expires_at=shared_resource.expires_at.isoformat() if shared_resource.expires_at else None
        )
    except Exception as e:
        logger.error(f"Error sharing resource: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to share resource: {str(e)}"
        )


@router.get("/collab/shared", response_model=List[ShareResponse])
async def list_shared_resources(
    resource_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List resources shared by the current user.
    
    Args:
        resource_type: Optional filter by resource type
    """
    query = db.query(SharedResource).filter(SharedResource.owner_id == current_user.id)
    
    if resource_type:
        query = query.filter(SharedResource.resource_type == resource_type)
    
    shared_resources = query.all()
    
    base_url = os.getenv("BASE_URL", "http://localhost:8080")
    
    return [
        ShareResponse(
            id=sr.id,
            resource_type=sr.resource_type,
            resource_id=sr.resource_id,
            permission=sr.permission,
            share_token=sr.share_token,
            share_url=f"{base_url}/shared/{sr.share_token}" if sr.share_token else None,
            expires_at=sr.expires_at.isoformat() if sr.expires_at else None
        )
        for sr in shared_resources
    ]

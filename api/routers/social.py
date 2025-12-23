"""Social media management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from api.database import get_db
from api.auth import get_current_user
from api.models import User
from api.schemas import SocialPostRequest, SocialPostResponse
from api.capabilities import capability_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/social", tags=["social_media"])


@router.post("/post", response_model=SocialPostResponse)
async def post_to_social(
    request: SocialPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Post content to social media platform."""
    if not capability_manager.is_enabled('social_media'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Social media capability is not enabled"
        )
    
    # Check if platform is supported
    platforms = capability_manager.capabilities.get('social_media', {}).get('platforms', [])
    if request.platform not in platforms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Platform '{request.platform}' is not supported"
        )
    
    try:
        # TODO: Integrate with social media APIs
        from api.integrations.social import post_to_platform
        
        result = await post_to_platform(
            platform=request.platform,
            content=request.content,
            media_urls=request.media_urls,
            user=current_user
        )
        
        return SocialPostResponse(**result)
    
    except Exception as e:
        logger.error(f"Error posting to {request.platform}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error posting to {request.platform}: {str(e)}"
        )


@router.post("/schedule", response_model=SocialPostResponse)
async def schedule_social_post(
    request: SocialPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule a social media post."""
    if not capability_manager.is_enabled('social_media'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Social media capability is not enabled"
        )
    
    if not request.scheduled_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scheduled_at is required for scheduling posts"
        )
    
    try:
        # TODO: Implement post scheduling
        return SocialPostResponse(
            platform=request.platform,
            post_id="scheduled_" + str(datetime.utcnow().timestamp()),
            url="#",
            status="scheduled",
            posted_at=request.scheduled_at
        )
    
    except Exception as e:
        logger.error(f"Error scheduling post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling post: {str(e)}"
        )

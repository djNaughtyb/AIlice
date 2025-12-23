"""Search and discovery endpoints."""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

from api.database import get_db
from api.auth import get_current_user
from api.models import User, Item, MediaFile, FileUpload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


class SearchResult(BaseModel):
    """Search result item."""
    id: int
    type: str  # item, media, file
    title: str
    description: Optional[str] = None
    created_at: str
    score: float = 1.0  # Relevance score


class RecommendationResponse(BaseModel):
    """Recommendation response."""
    id: int
    type: str
    title: str
    description: Optional[str] = None
    reason: str  # Why this is recommended


@router.get("/search", response_model=List[SearchResult])
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    type: Optional[str] = Query(None, description="Filter by type: item, media, file"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search across all user's content.
    
    Args:
        q: Search query string
        type: Optional filter by content type
        limit: Maximum number of results
    """
    results = []
    search_term = f"%{q.lower()}%"
    
    # Search in items
    if not type or type == "item":
        items = db.query(Item).filter(
            Item.user_id == current_user.id,
            or_(
                Item.title.ilike(search_term),
                Item.description.ilike(search_term)
            )
        ).limit(limit).all()
        
        for item in items:
            results.append(SearchResult(
                id=item.id,
                type="item",
                title=item.title,
                description=item.description,
                created_at=item.created_at.isoformat(),
                score=1.0
            ))
    
    # Search in media files
    if not type or type == "media":
        media_files = db.query(MediaFile).filter(
            MediaFile.user_id == current_user.id,
            MediaFile.original_filename.ilike(search_term)
        ).limit(limit).all()
        
        for media in media_files:
            results.append(SearchResult(
                id=media.id,
                type="media",
                title=media.original_filename,
                description=f"{media.media_type} - {media.mime_type}",
                created_at=media.created_at.isoformat(),
                score=0.9
            ))
    
    # Search in file uploads
    if not type or type == "file":
        files = db.query(FileUpload).filter(
            FileUpload.user_id == current_user.id,
            or_(
                FileUpload.original_filename.ilike(search_term),
                FileUpload.description.ilike(search_term)
            )
        ).limit(limit).all()
        
        for file in files:
            results.append(SearchResult(
                id=file.id,
                type="file",
                title=file.original_filename,
                description=file.description,
                created_at=file.created_at.isoformat(),
                score=0.9
            ))
    
    # Sort by score and limit
    results.sort(key=lambda x: x.score, reverse=True)
    return results[:limit]


@router.get("/recommendations", response_model=List[RecommendationResponse])
async def get_recommendations(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized recommendations for the user.
    
    This is a simple implementation that recommends recently created items.
    In production, this could use ML models for better recommendations.
    
    Args:
        limit: Maximum number of recommendations
    """
    recommendations = []
    
    # Recommend recent items
    recent_items = db.query(Item).filter(
        Item.user_id == current_user.id,
        Item.status == "published"
    ).order_by(Item.created_at.desc()).limit(limit).all()
    
    for item in recent_items:
        recommendations.append(RecommendationResponse(
            id=item.id,
            type="item",
            title=item.title,
            description=item.description,
            reason="Recently published"
        ))
    
    # If not enough items, recommend recent media
    if len(recommendations) < limit:
        remaining = limit - len(recommendations)
        recent_media = db.query(MediaFile).filter(
            MediaFile.user_id == current_user.id
        ).order_by(MediaFile.created_at.desc()).limit(remaining).all()
        
        for media in recent_media:
            recommendations.append(RecommendationResponse(
                id=media.id,
                type="media",
                title=media.original_filename,
                description=f"{media.media_type} file",
                reason="Recently uploaded media"
            ))
    
    return recommendations

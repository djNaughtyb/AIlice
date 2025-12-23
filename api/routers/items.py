"""Content/Data CRUD endpoints for items."""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from api.auth import get_current_user
from api.models import User, Item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/items", tags=["items"])


# Pydantic schemas
class ItemCreate(BaseModel):
    """Request body for creating an item."""
    title: str
    description: Optional[str] = None
    content: Optional[dict] = None
    item_type: str
    status: str = "draft"
    metadata: Optional[dict] = None


class ItemUpdate(BaseModel):
    """Request body for updating an item."""
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[dict] = None
    item_type: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None


class ItemResponse(BaseModel):
    """Response for item details."""
    id: int
    title: str
    description: Optional[str] = None
    content: Optional[dict] = None
    item_type: str
    status: str
    user_id: int
    metadata: Optional[dict] = None
    created_at: str
    updated_at: str
    published_at: Optional[str] = None

    class Config:
        from_attributes = True


# Endpoints
@router.get("", response_model=List[ItemResponse])
async def list_items(
    item_type: Optional[str] = Query(None, description="Filter by item type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all items for the current user with optional filters."""
    query = db.query(Item).filter(Item.user_id == current_user.id)
    
    if item_type:
        query = query.filter(Item.item_type == item_type)
    if status:
        query = query.filter(Item.status == status)
    
    items = query.order_by(Item.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        ItemResponse(
            id=item.id,
            title=item.title,
            description=item.description,
            content=item.content,
            item_type=item.item_type,
            status=item.status,
            user_id=item.user_id,
            metadata=item.metadata,
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat(),
            published_at=item.published_at.isoformat() if item.published_at else None
        )
        for item in items
    ]


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_data: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new item."""
    try:
        item = Item(
            title=item_data.title,
            description=item_data.description,
            content=item_data.content,
            item_type=item_data.item_type,
            status=item_data.status,
            user_id=current_user.id,
            metadata=item_data.metadata,
            published_at=datetime.utcnow() if item_data.status == "published" else None
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        logger.info(f"Created item {item.id} for user {current_user.id}")
        
        return ItemResponse(
            id=item.id,
            title=item.title,
            description=item.description,
            content=item.content,
            item_type=item.item_type,
            status=item.status,
            user_id=item.user_id,
            metadata=item.metadata,
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat(),
            published_at=item.published_at.isoformat() if item.published_at else None
        )
    except Exception as e:
        logger.error(f"Error creating item: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create item: {str(e)}"
        )


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific item by ID."""
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    return ItemResponse(
        id=item.id,
        title=item.title,
        description=item.description,
        content=item.content,
        item_type=item.item_type,
        status=item.status,
        user_id=item.user_id,
        metadata=item.metadata,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
        published_at=item.published_at.isoformat() if item.published_at else None
    )


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_data: ItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing item."""
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    try:
        # Update fields
        if item_data.title is not None:
            item.title = item_data.title
        if item_data.description is not None:
            item.description = item_data.description
        if item_data.content is not None:
            item.content = item_data.content
        if item_data.item_type is not None:
            item.item_type = item_data.item_type
        if item_data.status is not None:
            item.status = item_data.status
            if item_data.status == "published" and not item.published_at:
                item.published_at = datetime.utcnow()
        if item_data.metadata is not None:
            item.metadata = item_data.metadata
        
        item.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(item)
        
        logger.info(f"Updated item {item.id}")
        
        return ItemResponse(
            id=item.id,
            title=item.title,
            description=item.description,
            content=item.content,
            item_type=item.item_type,
            status=item.status,
            user_id=item.user_id,
            metadata=item.metadata,
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat(),
            published_at=item.published_at.isoformat() if item.published_at else None
        )
    except Exception as e:
        logger.error(f"Error updating item: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item: {str(e)}"
        )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an item."""
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    try:
        db.delete(item)
        db.commit()
        logger.info(f"Deleted item {item_id}")
        return None
    except Exception as e:
        logger.error(f"Error deleting item: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete item: {str(e)}"
        )

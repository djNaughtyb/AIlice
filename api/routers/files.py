"""File management endpoints."""
import os
import logging
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from api.auth import get_current_user
from api.models import User, FileUpload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 104857600))  # 100MB

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


class FileUploadResponse(BaseModel):
    """Response for file upload."""
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    description: Optional[str] = None
    tags: Optional[list] = None
    created_at: str

    class Config:
        from_attributes = True


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a file.
    
    Args:
        file: File to upload
        description: Optional file description
        tags: Optional comma-separated tags
    """
    try:
        # Check file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {MAX_UPLOAD_SIZE} bytes"
            )
        
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
        
        # Create database record
        file_upload = FileUpload(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            user_id=current_user.id,
            description=description,
            tags=tag_list
        )
        
        db.add(file_upload)
        db.commit()
        db.refresh(file_upload)
        
        logger.info(f"Uploaded file {file_upload.id} for user {current_user.id}")
        
        return FileUploadResponse(
            id=file_upload.id,
            filename=file_upload.filename,
            original_filename=file_upload.original_filename,
            file_size=file_upload.file_size,
            mime_type=file_upload.mime_type,
            description=file_upload.description,
            tags=file_upload.tags,
            created_at=file_upload.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("", response_model=List[FileUploadResponse])
async def list_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all files for the current user."""
    files = db.query(FileUpload).filter(
        FileUpload.user_id == current_user.id
    ).order_by(FileUpload.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        FileUploadResponse(
            id=f.id,
            filename=f.filename,
            original_filename=f.original_filename,
            file_size=f.file_size,
            mime_type=f.mime_type,
            description=f.description,
            tags=f.tags,
            created_at=f.created_at.isoformat()
        )
        for f in files
    ]


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a file.
    
    Args:
        file_id: File ID
    """
    file_upload = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.user_id == current_user.id
    ).first()
    
    if not file_upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not os.path.exists(file_upload.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        file_upload.file_path,
        media_type=file_upload.mime_type,
        filename=file_upload.original_filename
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a file.
    
    Args:
        file_id: File ID
    """
    file_upload = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.user_id == current_user.id
    ).first()
    
    if not file_upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        # Delete file from disk
        if os.path.exists(file_upload.file_path):
            os.remove(file_upload.file_path)
        
        # Delete database record
        db.delete(file_upload)
        db.commit()
        
        logger.info(f"Deleted file {file_id}")
        return None
    except Exception as e:
        logger.error(f"Error deleting file: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

"""Media handling endpoints with FFmpeg integration."""
import os
import logging
import uuid
import shutil
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import ffmpeg
from PIL import Image

from api.database import get_db
from api.auth import get_current_user
from api.models import User, MediaFile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/media", tags=["media"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 104857600))  # 100MB

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


class MediaResponse(BaseModel):
    """Response for media file details."""
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    media_type: str
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    transcoded: bool
    created_at: str

    class Config:
        from_attributes = True


class TranscodeRequest(BaseModel):
    """Request for transcoding media."""
    output_format: str
    quality: Optional[str] = "medium"  # low, medium, high


@router.post("/upload", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a media file (video, audio, or image)."""
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
        
        # Determine media type
        mime_type = file.content_type or "application/octet-stream"
        if mime_type.startswith("video/"):
            media_type = "video"
        elif mime_type.startswith("audio/"):
            media_type = "audio"
        elif mime_type.startswith("image/"):
            media_type = "image"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported media type. Only video, audio, and image files are allowed."
            )
        
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get media metadata
        duration = None
        width = None
        height = None
        
        if media_type in ["video", "audio"]:
            try:
                probe = ffmpeg.probe(file_path)
                if media_type == "video":
                    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
                    width = int(video_info['width'])
                    height = int(video_info['height'])
                    duration = int(float(probe['format']['duration']))
                elif media_type == "audio":
                    duration = int(float(probe['format']['duration']))
            except Exception as e:
                logger.warning(f"Could not probe media file: {e}")
        elif media_type == "image":
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
            except Exception as e:
                logger.warning(f"Could not get image dimensions: {e}")
        
        # Create database record
        media_file = MediaFile(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            media_type=media_type,
            duration=duration,
            width=width,
            height=height,
            user_id=current_user.id
        )
        
        db.add(media_file)
        db.commit()
        db.refresh(media_file)
        
        logger.info(f"Uploaded media file {media_file.id} for user {current_user.id}")
        
        return MediaResponse(
            id=media_file.id,
            filename=media_file.filename,
            original_filename=media_file.original_filename,
            file_size=media_file.file_size,
            mime_type=media_file.mime_type,
            media_type=media_file.media_type,
            duration=media_file.duration,
            width=media_file.width,
            height=media_file.height,
            transcoded=media_file.transcoded,
            created_at=media_file.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading media: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload media: {str(e)}"
        )


@router.get("/{media_id}/stream")
async def stream_media(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stream a media file."""
    media_file = db.query(MediaFile).filter(
        MediaFile.id == media_id,
        MediaFile.user_id == current_user.id
    ).first()
    
    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )
    
    if not os.path.exists(media_file.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found on disk"
        )
    
    def iterfile():
        with open(media_file.file_path, mode="rb") as file_like:
            yield from file_like
    
    return StreamingResponse(
        iterfile(),
        media_type=media_file.mime_type,
        headers={
            "Content-Disposition": f"inline; filename={media_file.original_filename}"
        }
    )


@router.post("/{media_id}/transcode", response_model=MediaResponse)
async def transcode_media(
    media_id: int,
    transcode_request: TranscodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Transcode a media file to a different format."""
    media_file = db.query(MediaFile).filter(
        MediaFile.id == media_id,
        MediaFile.user_id == current_user.id
    ).first()
    
    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )
    
    if media_file.media_type not in ["video", "audio"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only video and audio files can be transcoded"
        )
    
    try:
        # Generate output filename
        output_ext = transcode_request.output_format
        output_filename = f"{uuid.uuid4()}.{output_ext}"
        output_path = os.path.join(UPLOAD_DIR, output_filename)
        
        # Quality settings
        quality_settings = {
            "low": {"video_bitrate": "500k", "audio_bitrate": "96k"},
            "medium": {"video_bitrate": "1500k", "audio_bitrate": "192k"},
            "high": {"video_bitrate": "3000k", "audio_bitrate": "320k"},
        }
        quality = quality_settings.get(transcode_request.quality, quality_settings["medium"])
        
        # Transcode using FFmpeg
        if media_file.media_type == "video":
            stream = ffmpeg.input(media_file.file_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                video_bitrate=quality["video_bitrate"],
                audio_bitrate=quality["audio_bitrate"]
            )
            ffmpeg.run(stream, overwrite_output=True)
        else:  # audio
            stream = ffmpeg.input(media_file.file_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                audio_bitrate=quality["audio_bitrate"]
            )
            ffmpeg.run(stream, overwrite_output=True)
        
        # Update database record
        media_file.transcoded = True
        media_file.transcoded_path = output_path
        db.commit()
        db.refresh(media_file)
        
        logger.info(f"Transcoded media file {media_id}")
        
        return MediaResponse(
            id=media_file.id,
            filename=media_file.filename,
            original_filename=media_file.original_filename,
            file_size=media_file.file_size,
            mime_type=media_file.mime_type,
            media_type=media_file.media_type,
            duration=media_file.duration,
            width=media_file.width,
            height=media_file.height,
            transcoded=media_file.transcoded,
            created_at=media_file.created_at.isoformat()
        )
    except Exception as e:
        logger.error(f"Error transcoding media: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transcode media: {str(e)}"
        )

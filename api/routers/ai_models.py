"""AI model integration endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from api.database import get_db
from api.auth import get_current_user
from api.models import User
from api.schemas import AIModelRequest, AIModelResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai_models"])


@router.post("/replicate", response_model=AIModelResponse)
async def call_replicate_model(
    request: AIModelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Call Replicate API for model inference."""
    try:
        from api.integrations.replicate_api import call_replicate
        
        result = await call_replicate(
            model=request.model,
            prompt=request.prompt,
            parameters=request.parameters or {}
        )
        
        return AIModelResponse(**result)
    
    except Exception as e:
        logger.error(f"Error calling Replicate API: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calling Replicate API: {str(e)}"
        )


@router.post("/gemini", response_model=AIModelResponse)
async def call_gemini_model(
    request: AIModelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Call Google Gemini API for model inference."""
    try:
        from api.integrations.gemini_api import call_gemini
        
        result = await call_gemini(
            model=request.model,
            prompt=request.prompt,
            parameters=request.parameters or {}
        )
        
        return AIModelResponse(**result)
    
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calling Gemini API: {str(e)}"
        )


@router.get("/models")
async def list_available_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List available AI models."""
    return {
        "replicate": [
            "stability-ai/sdxl",
            "meta/llama-2-70b-chat",
            "openai/whisper"
        ],
        "gemini": [
            "gemini-pro",
            "gemini-pro-vision"
        ],
        "ollama": []  # Dynamically loaded from config
    }

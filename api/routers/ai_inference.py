"""AI/ML inference endpoints."""
import os
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import replicate
import google.generativeai as genai
from openai import OpenAI

from api.database import get_db
from api.auth import get_current_user
from api.models import User, AIModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai-inference"])

# Configure API clients
replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN", ""))
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


class PredictRequest(BaseModel):
    """Request body for prediction."""
    model_id: str
    input_data: Dict[str, Any]
    parameters: Optional[Dict[str, Any]] = None


class PredictResponse(BaseModel):
    """Response for prediction."""
    model_id: str
    output: Any
    metadata: Optional[Dict[str, Any]] = None


class TrainRequest(BaseModel):
    """Request body for model training."""
    model_name: str
    model_type: str
    base_model: str
    training_data: Dict[str, Any]
    parameters: Optional[Dict[str, Any]] = None


class TrainResponse(BaseModel):
    """Response for training."""
    training_id: str
    status: str
    message: str


class ModelResponse(BaseModel):
    """Response for model details."""
    id: int
    name: str
    model_type: str
    provider: str
    model_id: str
    version: Optional[str] = None
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/predict", response_model=PredictResponse)
async def predict(
    request: PredictRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run inference on an AI model.
    
    Supports multiple providers: Replicate, OpenAI, Google Gemini.
    """
    try:
        # Detect provider from model_id format
        if request.model_id.startswith("replicate:"):
            # Replicate model
            model_name = request.model_id.replace("replicate:", "")
            output = replicate_client.run(
                model_name,
                input=request.input_data
            )
            
            return PredictResponse(
                model_id=request.model_id,
                output=output,
                metadata={"provider": "replicate"}
            )
        
        elif request.model_id.startswith("openai:"):
            # OpenAI model
            model_name = request.model_id.replace("openai:", "")
            
            if "prompt" in request.input_data:
                response = openai_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": request.input_data["prompt"]}],
                    **(request.parameters or {})
                )
                output = response.choices[0].message.content
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing 'prompt' in input_data for OpenAI models"
                )
            
            return PredictResponse(
                model_id=request.model_id,
                output=output,
                metadata={"provider": "openai"}
            )
        
        elif request.model_id.startswith("google:"):
            # Google Gemini model
            model_name = request.model_id.replace("google:", "")
            model = genai.GenerativeModel(model_name)
            
            if "prompt" in request.input_data:
                response = model.generate_content(request.input_data["prompt"])
                output = response.text
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing 'prompt' in input_data for Google models"
                )
            
            return PredictResponse(
                model_id=request.model_id,
                output=output,
                metadata={"provider": "google"}
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unknown model provider. Use format: provider:model-name (e.g., openai:gpt-4, replicate:..., google:gemini-pro)"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running prediction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run prediction: {str(e)}"
        )


@router.post("/train", response_model=TrainResponse)
async def train_model(
    request: TrainRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Train a custom AI model.
    
    Note: This is a placeholder for model training functionality.
    Actual implementation would depend on the training infrastructure.
    """
    try:
        # This is a simplified implementation
        # In production, this would queue a training job
        
        # Create model record
        ai_model = AIModel(
            name=request.model_name,
            model_type=request.model_type,
            provider="custom",
            model_id=f"custom:{request.model_name}",
            description=f"Custom {request.model_type} model",
            config={
                "base_model": request.base_model,
                "training_parameters": request.parameters
            },
            is_active=False,  # Will be activated after training
            created_by=current_user.id
        )
        
        db.add(ai_model)
        db.commit()
        db.refresh(ai_model)
        
        logger.info(f"Queued training for model {ai_model.id}")
        
        return TrainResponse(
            training_id=str(ai_model.id),
            status="queued",
            message="Training job queued. You will be notified when complete."
        )
    
    except Exception as e:
        logger.error(f"Error training model: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start training: {str(e)}"
        )


@router.get("/models", response_model=List[ModelResponse])
async def list_models(
    model_type: Optional[str] = None,
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List available AI models.
    
    Args:
        model_type: Filter by model type (text, image, audio, video)
        provider: Filter by provider
    """
    query = db.query(AIModel).filter(AIModel.is_active == True)
    
    if model_type:
        query = query.filter(AIModel.model_type == model_type)
    if provider:
        query = query.filter(AIModel.provider == provider)
    
    models = query.all()
    
    return [
        ModelResponse(
            id=model.id,
            name=model.name,
            model_type=model.model_type,
            provider=model.provider,
            model_id=model.model_id,
            version=model.version,
            description=model.description,
            is_active=model.is_active
        )
        for model in models
    ]

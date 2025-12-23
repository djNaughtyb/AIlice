"""Replicate API integration."""
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def call_replicate(
    model: str,
    prompt: str,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Call Replicate API for model inference.
    
    Requires: pip install replicate
    Set REPLICATE_API_TOKEN environment variable
    """
    try:
        import replicate
        
        api_token = os.getenv("REPLICATE_API_TOKEN")
        if not api_token:
            raise ValueError("REPLICATE_API_TOKEN not set")
        
        # Initialize client
        client = replicate.Client(api_token=api_token)
        
        # Run model
        input_data = {"prompt": prompt}
        if parameters:
            input_data.update(parameters)
        
        output = client.run(model, input=input_data)
        
        # Format response
        if isinstance(output, str):
            response_text = output
        elif isinstance(output, list):
            response_text = "".join(str(item) for item in output)
        else:
            response_text = str(output)
        
        result = {
            "model": model,
            "response": response_text,
            "tokens_used": None,  # Replicate doesn't provide token count
            "cost": None
        }
        
        logger.info(f"Called Replicate model: {model}")
        return result
    
    except ImportError:
        logger.warning("Replicate library not installed. Install with: pip install replicate")
        # Return mock response
        return {
            "model": model,
            "response": f"[Mock] Response from {model}: {prompt[:50]}...",
            "tokens_used": None,
            "cost": None
        }
    
    except Exception as e:
        logger.error(f"Error calling Replicate API: {e}")
        raise

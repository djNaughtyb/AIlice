"""Google Gemini API integration."""
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def call_gemini(
    model: str,
    prompt: str,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Call Google Gemini API for model inference.
    
    Requires: pip install google-generativeai
    Set GEMINI_API_KEY environment variable
    """
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        # Configure API
        genai.configure(api_key=api_key)
        
        # Initialize model
        gemini_model = genai.GenerativeModel(model)
        
        # Set generation config
        generation_config = parameters or {}
        
        # Generate response
        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        # Extract text from response
        response_text = response.text
        
        # Try to get token count if available
        tokens_used = None
        if hasattr(response, 'usage_metadata'):
            tokens_used = getattr(response.usage_metadata, 'total_token_count', None)
        
        result = {
            "model": model,
            "response": response_text,
            "tokens_used": tokens_used,
            "cost": None  # Calculate based on pricing
        }
        
        logger.info(f"Called Gemini model: {model}")
        return result
    
    except ImportError:
        logger.warning("Google Generative AI library not installed. Install with: pip install google-generativeai")
        # Return mock response
        return {
            "model": model,
            "response": f"[Mock] Response from Gemini {model}: {prompt[:50]}...",
            "tokens_used": None,
            "cost": None
        }
    
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        raise

"""Rate limiting middleware for FastAPI."""
import time
from typing import Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from api.capabilities import capability_manager
from api.auth import decode_token
from api.database import get_db_context
from api.models import User

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting based on capabilities."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and check rate limits."""
        start_time = time.time()
        
        # Get capability for this endpoint
        capability = self._get_capability_for_endpoint(request.url.path)
        
        if capability:
            # Extract user from token
            user = await self._get_user_from_request(request)
            
            if user:
                # Check if capability is enabled
                if not capability_manager.is_enabled(capability):
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": f"Capability '{capability}' is not enabled"}
                    )
                
                # Check rate limit
                with get_db_context() as db:
                    if not capability_manager.check_rate_limit(db, user, capability):
                        return JSONResponse(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            content={
                                "detail": "Rate limit exceeded",
                                "capability": capability,
                                "rate_limit": capability_manager.get_rate_limit(capability)
                            }
                        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Record usage if applicable
            if capability and user:
                response_time = int((time.time() - start_time) * 1000)
                with get_db_context() as db:
                    capability_manager.record_usage(
                        db=db,
                        user=user,
                        capability=capability,
                        endpoint=request.url.path,
                        success=(200 <= response.status_code < 400),
                        response_time=response_time
                    )
            
            return response
        
        except Exception as e:
            logger.error(f"Error in rate limit middleware: {e}")
            
            # Record failed usage
            if capability and user:
                with get_db_context() as db:
                    capability_manager.record_usage(
                        db=db,
                        user=user,
                        capability=capability,
                        endpoint=request.url.path,
                        success=False,
                        error_message=str(e)
                    )
            
            raise
    
    def _get_capability_for_endpoint(self, path: str) -> str:
        """Get capability name for endpoint path."""
        for capability_name, config in capability_manager.capabilities.items():
            endpoints = config.get('endpoints', [])
            for endpoint in endpoints:
                if path.startswith(endpoint):
                    return capability_name
        return None
    
    async def _get_user_from_request(self, request: Request) -> User:
        """Extract user from request authorization header."""
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return None
            
            token = auth_header.split(' ')[1]
            payload = decode_token(token)
            username = payload.get('sub')
            
            if not username:
                return None
            
            with get_db_context() as db:
                user = db.query(User).filter(User.username == username).first()
                return user
        
        except Exception as e:
            logger.debug(f"Could not extract user from request: {e}")
            return None

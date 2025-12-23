"""System and admin endpoints."""
import os
import sys
import logging
import psutil
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from api.auth import get_current_user
from api.models import User, UserRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["system"])


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    uptime: float
    timestamp: str


class SystemStats(BaseModel):
    """System statistics."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    python_version: str


class ConfigResponse(BaseModel):
    """System configuration response."""
    environment: str
    debug_mode: bool
    max_upload_size: int
    stripe_enabled: bool
    redis_enabled: bool


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    System health check endpoint.
    
    This endpoint can be used for monitoring and load balancer health checks.
    """
    # Calculate uptime
    boot_time = psutil.boot_time()
    uptime = datetime.now().timestamp() - boot_time
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=uptime,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: User = Depends(require_admin)
):
    """
    Get system statistics (admin only).
    
    Returns CPU, memory, and disk usage statistics.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return SystemStats(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            python_version=sys.version
        )
    except Exception as e:
        logger.error(f"Error getting system stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {str(e)}"
        )


@router.get("/config", response_model=ConfigResponse)
async def get_system_config(
    current_user: User = Depends(require_admin)
):
    """
    Get system configuration (admin only).
    """
    return ConfigResponse(
        environment=os.getenv("ENVIRONMENT", "production"),
        debug_mode=os.getenv("ENVIRONMENT") == "development",
        max_upload_size=int(os.getenv("MAX_UPLOAD_SIZE", 104857600)),
        stripe_enabled=bool(os.getenv("STRIPE_SECRET_KEY")),
        redis_enabled=bool(os.getenv("REDIS_URL"))
    )


@router.post("/restart")
async def restart_system(
    current_user: User = Depends(require_admin)
):
    """
    Restart the system (admin only).
    
    Note: This is a placeholder. Actual restart would depend on deployment environment.
    """
    logger.warning(f"System restart requested by user {current_user.id}")
    
    return {
        "message": "System restart initiated. This may take a few moments.",
        "note": "In production, this would trigger a graceful restart of the service."
    }


@router.get("/logs")
async def get_recent_logs(
    lines: int = 100,
    current_user: User = Depends(require_admin)
):
    """
    Get recent system logs (admin only).
    
    Args:
        lines: Number of log lines to return
    """
    try:
        log_file = "/app/logs/ailice.log"
        
        if not os.path.exists(log_file):
            return {"logs": [], "message": "Log file not found"}
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
        
        return {
            "logs": recent_lines,
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines)
        }
    except Exception as e:
        logger.error(f"Error reading logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read logs: {str(e)}"
        )

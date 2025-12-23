"""Admin dashboard endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import logging

from api.database import get_db
from api.auth import require_admin
from api.models import User, Application, CapabilityUsage
from api.schemas import SystemStats, CapabilitiesResponse, CapabilityConfig
from api.capabilities import capability_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system statistics."""
    try:
        # Count users
        total_users = db.query(func.count(User.id)).scalar()
        active_users = db.query(func.count(User.id)).filter(
            User.is_active == True
        ).scalar()
        
        # Count applications
        total_apps = db.query(func.count(Application.id)).scalar()
        deployed_apps = db.query(func.count(Application.id)).filter(
            Application.status == "deployed"
        ).scalar()
        
        # Count API calls today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        api_calls_today = db.query(func.count(CapabilityUsage.id)).filter(
            CapabilityUsage.timestamp >= today
        ).scalar()
        
        # Get capabilities status
        capabilities_status = {
            name: config.get('enabled', False)
            for name, config in capability_manager.capabilities.items()
        }
        
        return SystemStats(
            total_users=total_users,
            active_users=active_users,
            total_applications=total_apps,
            deployed_applications=deployed_apps,
            api_calls_today=api_calls_today,
            capabilities_status=capabilities_status
        )
    
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting system stats: {str(e)}"
        )


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all capabilities configuration."""
    capabilities = {}
    for name, config in capability_manager.capabilities.items():
        capabilities[name] = CapabilityConfig(**config)
    
    return CapabilitiesResponse(capabilities=capabilities)


@router.put("/capabilities/{capability_name}")
async def update_capability(
    capability_name: str,
    config: CapabilityConfig,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update capability configuration."""
    try:
        capability_manager.update_capability(
            db=db,
            capability=capability_name,
            config=config.model_dump(),
            user=current_user
        )
        
        return {
            "message": f"Capability '{capability_name}' updated successfully",
            "capability": capability_name,
            "config": config.model_dump()
        }
    
    except Exception as e:
        logger.error(f"Error updating capability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating capability: {str(e)}"
        )


@router.get("/users")
async def list_all_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users."""
    users = db.query(User).all()
    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at
            }
            for user in users
        ]
    }


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user role."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    from api.models import UserRole
    try:
        user.role = UserRole(role)
        db.commit()
        
        return {
            "message": "User role updated successfully",
            "user_id": user_id,
            "new_role": role
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role}"
        )


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user active status."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = is_active
    db.commit()
    
    return {
        "message": "User status updated successfully",
        "user_id": user_id,
        "is_active": is_active
    }

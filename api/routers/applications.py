"""Application registry endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.auth import get_current_user, require_admin
from api.models import Application, User
from api.schemas import ApplicationCreate, ApplicationUpdate, ApplicationResponse

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    app_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new application."""
    # Check if subdomain is already taken
    if app_data.subdomain:
        existing = db.query(Application).filter(
            Application.subdomain == app_data.subdomain
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subdomain already taken"
            )
    
    # Create application
    app = Application(
        name=app_data.name,
        description=app_data.description,
        app_type=app_data.app_type,
        subdomain=app_data.subdomain,
        owner_id=current_user.id,
        config=app_data.config or {},
        status="pending"
    )
    
    db.add(app)
    db.commit()
    db.refresh(app)
    
    return ApplicationResponse.model_validate(app)


@router.get("/", response_model=List[ApplicationResponse])
async def list_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all applications for current user."""
    if current_user.role.value == "admin":
        # Admin can see all applications
        apps = db.query(Application).all()
    else:
        # Regular users see only their applications
        apps = db.query(Application).filter(
            Application.owner_id == current_user.id
        ).all()
    
    return [ApplicationResponse.model_validate(app) for app in apps]


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get application by ID."""
    app = db.query(Application).filter(Application.id == app_id).first()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check permission
    if app.owner_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this application"
        )
    
    return ApplicationResponse.model_validate(app)


@router.put("/{app_id}", response_model=ApplicationResponse)
async def update_application(
    app_id: int,
    app_data: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update application."""
    app = db.query(Application).filter(Application.id == app_id).first()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check permission
    if app.owner_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this application"
        )
    
    # Update fields
    update_data = app_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(app, field, value)
    
    db.commit()
    db.refresh(app)
    
    return ApplicationResponse.model_validate(app)


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete application."""
    app = db.query(Application).filter(Application.id == app_id).first()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check permission
    if app.owner_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this application"
        )
    
    db.delete(app)
    db.commit()

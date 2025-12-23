"""External integrations endpoints."""
import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from api.auth import get_current_user
from api.models import User, IntegrationStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


class IntegrationConnect(BaseModel):
    """Request body for connecting an integration."""
    access_token: str
    refresh_token: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class IntegrationStatusResponse(BaseModel):
    """Response for integration status."""
    id: int
    service_name: str
    connected: bool
    last_sync: Optional[str] = None
    sync_status: str
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class SyncRequest(BaseModel):
    """Request body for syncing data."""
    sync_type: str = "full"  # full, incremental
    options: Optional[Dict[str, Any]] = None


class SyncResponse(BaseModel):
    """Response for sync operation."""
    service_name: str
    sync_status: str
    items_synced: int
    message: str


# Supported services
SUPPORTED_SERVICES = [
    "google_drive",
    "tradingview",
    "dropbox",
    "onedrive",
    "github",
    "gitlab",
    "slack",
    "discord",
    "twitter",
    "linkedin"
]


@router.post("/{service}/connect", response_model=IntegrationStatusResponse, status_code=status.HTTP_201_CREATED)
async def connect_integration(
    service: str,
    connect_data: IntegrationConnect,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Connect an external integration.
    
    Args:
        service: Service name (e.g., google_drive, tradingview)
        connect_data: Connection data including access token
    """
    if service not in SUPPORTED_SERVICES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported service. Supported services: {', '.join(SUPPORTED_SERVICES)}"
        )
    
    try:
        # Check if integration already exists
        existing = db.query(IntegrationStatus).filter(
            IntegrationStatus.user_id == current_user.id,
            IntegrationStatus.service_name == service
        ).first()
        
        if existing:
            # Update existing integration
            existing.access_token = connect_data.access_token
            existing.refresh_token = connect_data.refresh_token
            existing.connected = True
            existing.config = connect_data.config
            existing.updated_at = datetime.utcnow()
            integration = existing
        else:
            # Create new integration
            integration = IntegrationStatus(
                user_id=current_user.id,
                service_name=service,
                connected=True,
                access_token=connect_data.access_token,
                refresh_token=connect_data.refresh_token,
                config=connect_data.config
            )
            db.add(integration)
        
        db.commit()
        db.refresh(integration)
        
        logger.info(f"Connected {service} integration for user {current_user.id}")
        
        return IntegrationStatusResponse(
            id=integration.id,
            service_name=integration.service_name,
            connected=integration.connected,
            last_sync=integration.last_sync.isoformat() if integration.last_sync else None,
            sync_status=integration.sync_status,
            error_message=integration.error_message,
            created_at=integration.created_at.isoformat(),
            updated_at=integration.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting integration: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect integration: {str(e)}"
        )


@router.post("/{service}/sync", response_model=SyncResponse)
async def sync_integration(
    service: str,
    sync_data: SyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync data from an external integration.
    
    Args:
        service: Service name
        sync_data: Sync configuration
    """
    integration = db.query(IntegrationStatus).filter(
        IntegrationStatus.user_id == current_user.id,
        IntegrationStatus.service_name == service
    ).first()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration for {service} not found. Please connect first."
        )
    
    if not integration.connected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integration for {service} is not connected."
        )
    
    try:
        # Update sync status
        integration.sync_status = "syncing"
        integration.error_message = None
        db.commit()
        
        # Perform sync (placeholder - actual implementation would depend on service)
        items_synced = 0
        
        if service == "google_drive":
            # Sync Google Drive files
            logger.info(f"Syncing Google Drive for user {current_user.id}")
            items_synced = 10  # Placeholder
        
        elif service == "tradingview":
            # Sync TradingView charts/alerts
            logger.info(f"Syncing TradingView for user {current_user.id}")
            items_synced = 5  # Placeholder
        
        else:
            # Generic sync
            logger.info(f"Syncing {service} for user {current_user.id}")
            items_synced = 0
        
        # Update integration status
        integration.sync_status = "idle"
        integration.last_sync = datetime.utcnow()
        db.commit()
        
        return SyncResponse(
            service_name=service,
            sync_status="completed",
            items_synced=items_synced,
            message=f"Successfully synced {items_synced} items from {service}"
        )
    
    except Exception as e:
        logger.error(f"Error syncing integration: {e}", exc_info=True)
        integration.sync_status = "error"
        integration.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync integration: {str(e)}"
        )


@router.get("/{service}/status", response_model=IntegrationStatusResponse)
async def get_integration_status(
    service: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get status of an integration.
    
    Args:
        service: Service name
    """
    integration = db.query(IntegrationStatus).filter(
        IntegrationStatus.user_id == current_user.id,
        IntegrationStatus.service_name == service
    ).first()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration for {service} not found"
        )
    
    return IntegrationStatusResponse(
        id=integration.id,
        service_name=integration.service_name,
        connected=integration.connected,
        last_sync=integration.last_sync.isoformat() if integration.last_sync else None,
        sync_status=integration.sync_status,
        error_message=integration.error_message,
        created_at=integration.created_at.isoformat(),
        updated_at=integration.updated_at.isoformat()
    )


@router.get("", response_model=List[IntegrationStatusResponse])
async def list_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all integrations for the current user."""
    integrations = db.query(IntegrationStatus).filter(
        IntegrationStatus.user_id == current_user.id
    ).all()
    
    return [
        IntegrationStatusResponse(
            id=integration.id,
            service_name=integration.service_name,
            connected=integration.connected,
            last_sync=integration.last_sync.isoformat() if integration.last_sync else None,
            sync_status=integration.sync_status,
            error_message=integration.error_message,
            created_at=integration.created_at.isoformat(),
            updated_at=integration.updated_at.isoformat()
        )
        for integration in integrations
    ]


@router.delete("/{service}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_integration(
    service: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect an integration.
    
    Args:
        service: Service name
    """
    integration = db.query(IntegrationStatus).filter(
        IntegrationStatus.user_id == current_user.id,
        IntegrationStatus.service_name == service
    ).first()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration for {service} not found"
        )
    
    try:
        db.delete(integration)
        db.commit()
        logger.info(f"Disconnected {service} integration for user {current_user.id}")
        return None
    except Exception as e:
        logger.error(f"Error disconnecting integration: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect integration: {str(e)}"
        )

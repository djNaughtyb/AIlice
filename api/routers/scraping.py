"""Web scraping endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from api.database import get_db
from api.auth import get_current_user
from api.models import User
from api.schemas import ScrapeRequest, ScrapeResponse
from api.capabilities import capability_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["web_scraping"])


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(
    request: ScrapeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Scrape a URL and return content."""
    if not capability_manager.is_enabled('web_scraping'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Web scraping capability is not enabled"
        )
    
    try:
        # TODO: Integrate with AIlice's web scraping module
        # For now, return a mock response
        from api.integrations.scraper import scrape_website
        
        result = await scrape_website(
            url=request.url,
            selector=request.selector,
            wait_for=request.wait_for,
            screenshot=request.screenshot
        )
        
        return ScrapeResponse(**result)
    
    except Exception as e:
        logger.error(f"Error scraping URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scraping URL: {str(e)}"
        )


@router.post("/browse")
async def browse_website(
    request: ScrapeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Browse a website interactively."""
    if not capability_manager.is_enabled('web_scraping'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Web scraping capability is not enabled"
        )
    
    try:
        # TODO: Integrate with AIlice's browser module
        return {
            "url": request.url,
            "status": "browsing",
            "message": "Browser session initiated"
        }
    
    except Exception as e:
        logger.error(f"Error browsing website: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error browsing website: {str(e)}"
        )

"""Analytics and metrics endpoints."""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from api.database import get_db
from api.auth import get_current_user
from api.models import User, AnalyticsEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class UsageStats(BaseModel):
    """Usage statistics response."""
    total_events: int
    api_calls: int
    page_views: int
    errors: int
    avg_response_time: float
    period_start: str
    period_end: str


class ErrorStat(BaseModel):
    """Error statistics."""
    endpoint: str
    error_count: int
    last_error: str
    last_occurred: str


class PerformanceStat(BaseModel):
    """Performance statistics."""
    endpoint: str
    avg_response_time: float
    min_response_time: int
    max_response_time: int
    total_calls: int


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get usage statistics for the current user.
    
    Args:
        days: Number of days to analyze (1-90)
    """
    period_start = datetime.utcnow() - timedelta(days=days)
    period_end = datetime.utcnow()
    
    # Query events
    events = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.user_id == current_user.id,
        AnalyticsEvent.created_at >= period_start
    ).all()
    
    total_events = len(events)
    api_calls = len([e for e in events if e.event_type == "api_call"])
    page_views = len([e for e in events if e.event_type == "page_view"])
    errors = len([e for e in events if e.event_type == "error"])
    
    # Calculate average response time
    response_times = [e.response_time for e in events if e.response_time is not None]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
    
    return UsageStats(
        total_events=total_events,
        api_calls=api_calls,
        page_views=page_views,
        errors=errors,
        avg_response_time=round(avg_response_time, 2),
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat()
    )


@router.get("/errors", response_model=List[ErrorStat])
async def get_error_stats(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get error statistics grouped by endpoint.
    
    Args:
        days: Number of days to analyze
        limit: Maximum number of results
    """
    period_start = datetime.utcnow() - timedelta(days=days)
    
    # Query error events
    errors = db.query(
        AnalyticsEvent.endpoint,
        func.count(AnalyticsEvent.id).label("error_count"),
        func.max(AnalyticsEvent.error_message).label("last_error"),
        func.max(AnalyticsEvent.created_at).label("last_occurred")
    ).filter(
        AnalyticsEvent.user_id == current_user.id,
        AnalyticsEvent.event_type == "error",
        AnalyticsEvent.created_at >= period_start
    ).group_by(
        AnalyticsEvent.endpoint
    ).order_by(
        func.count(AnalyticsEvent.id).desc()
    ).limit(limit).all()
    
    return [
        ErrorStat(
            endpoint=error.endpoint or "unknown",
            error_count=error.error_count,
            last_error=error.last_error or "No message",
            last_occurred=error.last_occurred.isoformat()
        )
        for error in errors
    ]


@router.get("/performance", response_model=List[PerformanceStat])
async def get_performance_stats(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get performance statistics grouped by endpoint.
    
    Args:
        days: Number of days to analyze
        limit: Maximum number of results
    """
    period_start = datetime.utcnow() - timedelta(days=days)
    
    # Query API call events with response times
    stats = db.query(
        AnalyticsEvent.endpoint,
        func.avg(AnalyticsEvent.response_time).label("avg_response_time"),
        func.min(AnalyticsEvent.response_time).label("min_response_time"),
        func.max(AnalyticsEvent.response_time).label("max_response_time"),
        func.count(AnalyticsEvent.id).label("total_calls")
    ).filter(
        AnalyticsEvent.user_id == current_user.id,
        AnalyticsEvent.event_type == "api_call",
        AnalyticsEvent.response_time.isnot(None),
        AnalyticsEvent.created_at >= period_start
    ).group_by(
        AnalyticsEvent.endpoint
    ).order_by(
        func.avg(AnalyticsEvent.response_time).desc()
    ).limit(limit).all()
    
    return [
        PerformanceStat(
            endpoint=stat.endpoint or "unknown",
            avg_response_time=round(float(stat.avg_response_time), 2),
            min_response_time=int(stat.min_response_time),
            max_response_time=int(stat.max_response_time),
            total_calls=stat.total_calls
        )
        for stat in stats
    ]

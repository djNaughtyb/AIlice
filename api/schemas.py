"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# User schemas
class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Application schemas
class ApplicationCreate(BaseModel):
    """Schema for creating application."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    app_type: str = Field(..., min_length=1)
    subdomain: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class ApplicationUpdate(BaseModel):
    """Schema for updating application."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class ApplicationResponse(BaseModel):
    """Schema for application response."""
    id: int
    name: str
    description: Optional[str]
    app_type: str
    status: str
    url: Optional[str]
    subdomain: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: datetime
    deployed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Capability schemas
class CapabilityConfig(BaseModel):
    """Schema for capability configuration."""
    enabled: bool
    permissions: Optional[List[str]] = None
    platforms: Optional[List[str]] = None
    providers: Optional[List[str]] = None
    rate_limit: Optional[str] = None
    requires_admin: Optional[bool] = False
    endpoints: List[str]
    description: Optional[str] = None


class CapabilitiesResponse(BaseModel):
    """Schema for capabilities response."""
    capabilities: Dict[str, CapabilityConfig]


# Web scraping schemas
class ScrapeRequest(BaseModel):
    """Schema for web scraping request."""
    url: str
    selector: Optional[str] = None
    wait_for: Optional[str] = None
    screenshot: bool = False


class ScrapeResponse(BaseModel):
    """Schema for scraping response."""
    url: str
    title: Optional[str]
    content: str
    screenshot_url: Optional[str]
    metadata: Dict[str, Any]


# Social media schemas
class SocialPostRequest(BaseModel):
    """Schema for social media post request."""
    platform: str = Field(..., regex="^(twitter|linkedin)$")
    content: str = Field(..., max_length=3000)
    media_urls: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None


class SocialPostResponse(BaseModel):
    """Schema for social media post response."""
    platform: str
    post_id: str
    url: str
    status: str
    posted_at: datetime


# Cloud management schemas
class DeploymentRequest(BaseModel):
    """Schema for deployment request."""
    provider: str = Field(..., regex="^(aws|gcp|digitalocean)$")
    app_id: int
    region: Optional[str] = None
    instance_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class DeploymentResponse(BaseModel):
    """Schema for deployment response."""
    deployment_id: str
    provider: str
    status: str
    url: Optional[str]
    created_at: datetime


# AI model schemas
class AIModelRequest(BaseModel):
    """Schema for AI model request."""
    model: str
    prompt: str
    parameters: Optional[Dict[str, Any]] = None


class AIModelResponse(BaseModel):
    """Schema for AI model response."""
    model: str
    response: str
    tokens_used: Optional[int]
    cost: Optional[float]


# System stats schemas
class SystemStats(BaseModel):
    """Schema for system statistics."""
    total_users: int
    active_users: int
    total_applications: int
    deployed_applications: int
    api_calls_today: int
    capabilities_status: Dict[str, bool]

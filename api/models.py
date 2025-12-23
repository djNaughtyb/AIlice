"""Database models for users, applications, and capabilities."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    """User roles for access control."""
    ADMIN = "admin"
    USER = "user"


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Rate limiting tracking
    api_calls_count = Column(Integer, default=0)
    last_api_reset = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = relationship("Application", back_populates="owner")
    api_keys = relationship("APIKey", back_populates="user")

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role.value}')>"


class APIKey(Base):
    """API keys for programmatic access."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(name='{self.name}', user_id={self.user_id})>"


class Application(Base):
    """Application registry for deployed applications."""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    app_type = Column(String(50), nullable=False)  # web, api, service, etc.
    status = Column(String(20), default="pending")  # pending, deployed, failed, stopped
    url = Column(String(255))
    subdomain = Column(String(100), unique=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    config = Column(JSON)  # Application-specific configuration
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deployed_at = Column(DateTime, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="applications")

    def __repr__(self):
        return f"<Application(name='{self.name}', status='{self.status}')>"


class CapabilityUsage(Base):
    """Track capability usage for rate limiting."""
    __tablename__ = "capability_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    capability = Column(String(50), nullable=False, index=True)
    endpoint = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    success = Column(Boolean, default=True)
    response_time = Column(Integer)  # milliseconds
    error_message = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<CapabilityUsage(user_id={self.user_id}, capability='{self.capability}')>"


class SystemConfig(Base):
    """System configuration and capability settings."""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(String(500))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<SystemConfig(key='{self.key}')>"


class SubscriptionStatus(enum.Enum):
    """Subscription status for Stripe subscriptions."""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"


class Subscription(Base):
    """Subscription model for Stripe payment tracking."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    stripe_customer_id = Column(String(100), nullable=False, index=True)
    stripe_subscription_id = Column(String(100), unique=True, nullable=False, index=True)
    stripe_price_id = Column(String(100), nullable=False)
    status = Column(Enum(SubscriptionStatus), nullable=False, index=True)
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Subscription(user_id={self.user_id}, status='{self.status.value}')>"


class Item(Base):
    """Generic content/data items for CRUD operations."""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(String(1000))
    content = Column(JSON)  # Flexible content storage
    item_type = Column(String(50), nullable=False, index=True)  # post, article, product, etc.
    status = Column(String(20), default="draft", index=True)  # draft, published, archived
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    metadata = Column(JSON)  # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Item(title='{self.title}', type='{self.item_type}')>"


class MediaFile(Base):
    """Media files for upload, streaming, and transcoding."""
    __tablename__ = "media_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    mime_type = Column(String(100), nullable=False)
    media_type = Column(String(20), nullable=False, index=True)  # video, audio, image
    duration = Column(Integer, nullable=True)  # seconds for video/audio
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    transcoded = Column(Boolean, default=False)
    transcoded_path = Column(String(500), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<MediaFile(filename='{self.filename}', type='{self.media_type}')>"


class Notification(Base):
    """Notifications for users."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(String(1000), nullable=False)
    notification_type = Column(String(50), nullable=False, index=True)  # info, warning, error, success
    read = Column(Boolean, default=False, index=True)
    action_url = Column(String(500), nullable=True)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Notification(user_id={self.user_id}, title='{self.title}')>"


class ChatMessage(Base):
    """Chat messages for collaboration."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message = Column(String(5000), nullable=False)
    message_type = Column(String(20), default="text")  # text, file, image, system
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    edited_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False)

    def __repr__(self):
        return f"<ChatMessage(room_id='{self.room_id}', user_id={self.user_id})>"


class FileUpload(Base):
    """File uploads for general file management."""
    __tablename__ = "file_uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    mime_type = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    description = Column(String(500))
    tags = Column(JSON)  # Array of tags
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<FileUpload(filename='{self.filename}', user_id={self.user_id})>"


class IntegrationStatus(Base):
    """Track status of external integrations."""
    __tablename__ = "integration_status"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)  # google_drive, tradingview, etc.
    connected = Column(Boolean, default=False)
    access_token = Column(String(500), nullable=True)  # Encrypted token
    refresh_token = Column(String(500), nullable=True)  # Encrypted token
    token_expires_at = Column(DateTime, nullable=True)
    last_sync = Column(DateTime, nullable=True)
    sync_status = Column(String(20), default="idle")  # idle, syncing, error
    error_message = Column(String(500), nullable=True)
    config = Column(JSON)  # Service-specific configuration
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<IntegrationStatus(service='{self.service_name}', connected={self.connected})>"


class AnalyticsEvent(Base):
    """Analytics events for tracking usage and performance."""
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for anonymous events
    event_type = Column(String(50), nullable=False, index=True)  # page_view, api_call, error, etc.
    event_name = Column(String(100), nullable=False, index=True)
    endpoint = Column(String(200), nullable=True)
    method = Column(String(10), nullable=True)  # GET, POST, etc.
    status_code = Column(Integer, nullable=True)
    response_time = Column(Integer, nullable=True)  # milliseconds
    error_message = Column(String(1000), nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<AnalyticsEvent(type='{self.event_type}', name='{self.event_name}')>"


class AIModel(Base):
    """AI/ML models registry."""
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    model_type = Column(String(50), nullable=False)  # text, image, audio, video
    provider = Column(String(50), nullable=False)  # openai, replicate, google, etc.
    model_id = Column(String(200), nullable=False)
    version = Column(String(50), nullable=True)
    description = Column(String(1000))
    config = Column(JSON)  # Model-specific configuration
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AIModel(name='{self.name}', provider='{self.provider}')>"


class SharedResource(Base):
    """Shared resources for collaboration."""
    __tablename__ = "shared_resources"

    id = Column(Integer, primary_key=True, index=True)
    resource_type = Column(String(50), nullable=False, index=True)  # item, file, chat_room, etc.
    resource_id = Column(Integer, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_with_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for public
    permission = Column(String(20), default="view")  # view, edit, admin
    share_token = Column(String(100), unique=True, nullable=True)  # For public sharing
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SharedResource(type='{self.resource_type}', id={self.resource_id})>"

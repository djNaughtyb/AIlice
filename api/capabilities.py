"""Capabilities configuration and management."""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session
from api.models import SystemConfig, CapabilityUsage, User

logger = logging.getLogger(__name__)


class CapabilityManager:
    """Manages capabilities and their configurations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize capability manager."""
        self.config_path = config_path or os.getenv(
            "CAPABILITIES_CONFIG",
            "/home/ubuntu/viralspark_ailice/capabilities_config.json"
        )
        self.capabilities = self._load_capabilities()
    
    def _load_capabilities(self) -> Dict:
        """Load capabilities from config file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('capabilities', {})
            else:
                logger.warning(f"Capabilities config not found at {self.config_path}")
                return self._get_default_capabilities()
        except Exception as e:
            logger.error(f"Error loading capabilities config: {e}")
            return self._get_default_capabilities()
    
    def _get_default_capabilities(self) -> Dict:
        """Get default capabilities configuration."""
        return {
            "web_scraping": {
                "enabled": True,
                "permissions": ["read", "write"],
                "rate_limit": "100/hour",
                "endpoints": ["/api/scrape", "/api/browse"]
            },
            "social_media": {
                "enabled": True,
                "platforms": ["twitter", "linkedin"],
                "rate_limit": "50/hour",
                "endpoints": ["/api/social/post", "/api/social/schedule"]
            },
            "cloud_management": {
                "enabled": False,
                "requires_admin": True,
                "endpoints": ["/api/cloud/deploy", "/api/cloud/manage"]
            }
        }
    
    def is_enabled(self, capability: str) -> bool:
        """Check if capability is enabled."""
        return self.capabilities.get(capability, {}).get('enabled', False)
    
    def get_rate_limit(self, capability: str) -> Optional[str]:
        """Get rate limit for capability."""
        return self.capabilities.get(capability, {}).get('rate_limit')
    
    def requires_admin(self, capability: str) -> bool:
        """Check if capability requires admin access."""
        return self.capabilities.get(capability, {}).get('requires_admin', False)
    
    def get_endpoints(self, capability: str) -> List[str]:
        """Get endpoints for capability."""
        return self.capabilities.get(capability, {}).get('endpoints', [])
    
    def check_rate_limit(self, db: Session, user: User, capability: str) -> bool:
        """Check if user has exceeded rate limit for capability."""
        rate_limit_str = self.get_rate_limit(capability)
        if not rate_limit_str:
            return True  # No rate limit
        
        # Parse rate limit (e.g., "100/hour")
        try:
            count, period = rate_limit_str.split('/')
            count = int(count)
            
            # Calculate time window
            if period == 'hour':
                time_window = timedelta(hours=1)
            elif period == 'day':
                time_window = timedelta(days=1)
            elif period == 'minute':
                time_window = timedelta(minutes=1)
            else:
                logger.warning(f"Unknown rate limit period: {period}")
                return True
            
            # Query usage in time window
            since = datetime.utcnow() - time_window
            usage_count = db.query(CapabilityUsage).filter(
                CapabilityUsage.user_id == user.id,
                CapabilityUsage.capability == capability,
                CapabilityUsage.timestamp >= since
            ).count()
            
            return usage_count < count
        
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error
    
    def record_usage(
        self,
        db: Session,
        user: User,
        capability: str,
        endpoint: str,
        success: bool = True,
        response_time: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Record capability usage."""
        try:
            usage = CapabilityUsage(
                user_id=user.id,
                capability=capability,
                endpoint=endpoint,
                success=success,
                response_time=response_time,
                error_message=error_message
            )
            db.add(usage)
            db.commit()
        except Exception as e:
            logger.error(f"Error recording usage: {e}")
            db.rollback()
    
    def update_capability(self, db: Session, capability: str, config: Dict, user: User):
        """Update capability configuration."""
        try:
            # Update in-memory config
            self.capabilities[capability] = config
            
            # Save to database
            system_config = db.query(SystemConfig).filter(
                SystemConfig.key == f"capability_{capability}"
            ).first()
            
            if system_config:
                system_config.value = config
                system_config.updated_by = user.id
            else:
                system_config = SystemConfig(
                    key=f"capability_{capability}",
                    value=config,
                    description=f"Configuration for {capability} capability",
                    updated_by=user.id
                )
                db.add(system_config)
            
            db.commit()
            
            # Save to file
            self._save_capabilities()
            
        except Exception as e:
            logger.error(f"Error updating capability: {e}")
            db.rollback()
            raise
    
    def _save_capabilities(self):
        """Save capabilities to config file."""
        try:
            config = {'capabilities': self.capabilities}
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving capabilities config: {e}")


# Global capability manager instance
capability_manager = CapabilityManager()

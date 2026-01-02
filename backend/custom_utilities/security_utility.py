import logging
from fastapi import Request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Constants
MAX_LOGIN_ATTEMPTS = 5

@dataclass
class SecurityEvent:
    """Data class for security event logging"""
    user_id: Optional[str]
    event_type: str
    ip_address: str
    success: bool
    details: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

class SecurityUtility:
    """Utility class for security-related operations"""

    # Rate limiting and security headers can be added here
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Extract client IP address from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    @staticmethod
    def log_activity(user_id: str, action: str, ip_address: str, success: bool = True):
        """Log user activities for security monitoring."""
        logger.info(f"User Activity - ID: {user_id}, Action: {action}, IP: {ip_address}, Success: {success}")
    
    @staticmethod
    def log_security_event(event: SecurityEvent) -> None:
        """Log security events for monitoring and audit purposes"""
        try:
            logger.info(
                f"SECURITY_EVENT - Type: {event.event_type}, "
                f"User: {event.user_id or 'unknown'}, "
                f"IP: {event.ip_address}, "
                f"Success: {event.success}, "
                f"Details: {event.details or 'none'}, "
                f"Timestamp: {event.timestamp}"
            )
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")

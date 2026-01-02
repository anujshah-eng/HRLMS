import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from repository.user_management import UserRepository

logger = logging.getLogger(__name__)

# Constants
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_DURATION = timedelta(minutes=1)


class AccountUtility:
    """Utility class for account management operations"""
    
    @staticmethod
    def is_account_locked(user_data: Any) -> bool:
        """Check if account is locked due to failed login attempts"""
        if not hasattr(user_data, 'failed_login_attempts') or not hasattr(user_data, 'locked_until'):
            return False
        
        if user_data.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            if user_data.locked_until and datetime.now(timezone.utc) < user_data.locked_until:
                return True
        
        return False

    @staticmethod
    def increment_failed_login(user_id: int) -> None:
        """Increment failed login attempts and lock account if necessary"""
        try:            
            UserRepository.increment_failed_login_attempts(user_id)
            failed_attempts = UserRepository.get_failed_login_attempts(user_id)
            
            if failed_attempts >= MAX_LOGIN_ATTEMPTS:
                lock_until = datetime.now(timezone.utc) + ACCOUNT_LOCKOUT_DURATION
                UserRepository.lock_account(user_id, lock_until)
                logger.warning(f"Account locked for user {user_id} due to {failed_attempts} failed attempts")
        except Exception as e:
            logger.error(f"Failed to increment login attempts for user {user_id}: {str(e)}")

    @staticmethod
    def reset_failed_login(user_id: int) -> None:
        """Reset failed login attempts after successful login"""
        try:
            UserRepository.reset_failed_login_attempts(user_id)
        except Exception as e:
            logger.error(f"Failed to reset login attempts for user {user_id}: {str(e)}")

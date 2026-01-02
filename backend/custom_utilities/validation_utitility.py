    
import re
import bcrypt
from typing import Any
from datetime import datetime, timezone
import logging
from custom_utilities.custom_exception import CustomException
from enums.quiz_system.questions import QuestionType

logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

class ValidationUtility:
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format with comprehensive regex"""
        if not email or len(email) > 254:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip().lower()))

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password strength with comprehensive checks
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
        
        if len(password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
        
        if len(password) > MAX_PASSWORD_LENGTH:
            return False, f"Password must not exceed {MAX_PASSWORD_LENGTH} characters"
        
        # Check for complexity requirements
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if not all([has_upper, has_lower, has_digit, has_special]):
            return False, "Password must contain uppercase, lowercase, digit, and special character"
        
        return True, ""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt with proper salt rounds"""
        try:
            # Use 12 rounds for good security/performance balance
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        except Exception as e:
            logger.error(f"Password hashing failed: {str(e)}")
            raise CustomException("Password processing failed", status_code=500)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password against hash with timing attack protection"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False
        
    @staticmethod
    def validate_mcq_or_true_false(final_options: list, correct_answer: str):
        """
        Validates that at least one option is marked correct.
        """
        if not final_options:
            raise CustomException(
                "MCQ/True-False questions must have at least one option.",
                status_code=400
            )
        if not correct_answer:
            raise CustomException(
                "MCQ/True-False questions must have correct answer.",
                status_code=400
            )

    @staticmethod
    def validate_open_ended(question_data: dict):
        """
        Validates that open-ended questions have a correct answer.
        """
        correct_answer = question_data.get("correct_answer")
        if correct_answer is None or not correct_answer.strip():
            raise CustomException(
                "Open-ended questions must have a non-empty correct answer.",
                status_code=400
            )

    @staticmethod
    def merge_options(existing_options: list, option_updates: list):
        """
        Merges partial option updates into existing options.

        :param existing_options: full list of current options
        :param option_updates: list of partial updates e.g. [{"order": 1, "text": "New Text"}]
        :return: new list of options reflecting updates
        """
        # Index by order
        options_by_order = {opt.order: opt.copy() for opt in existing_options}

        for update in option_updates:
            order = update['order']
            if order is None:
                raise CustomException(
                    "Each option update must include 'order'.",
                    status_code=400
                )
            if order not in options_by_order:
                raise CustomException(
                    f"Option with order {order} not found in existing options.",
                    status_code=404
                )
            
            # Apply updates to the existing option
            for key, value in update.items():
                if hasattr(options_by_order[order], key):
                    setattr(options_by_order[order], key, value)
        return list(options_by_order.values())

    @staticmethod
    def validate_question_update(
        question_type: str,
        question_updates: dict,
        option_updates: list,
        existing_options: list,
        correct_answer: str
    ):
        """
        Validates the updated question based on its type.
        """

        # Only validate if the fields relevant to correctness are involved
        if question_type in (QuestionType.MCQ, QuestionType.TRUE_FALSE):
            # merge existing options and updated options
            if existing_options:
                final_options = ValidationUtility.merge_options(existing_options, option_updates)
                ValidationUtility.validate_mcq_or_true_false(final_options, correct_answer)
        elif question_type == QuestionType.OPEN_ENDED:
            if "correct_answer" in question_updates:
                ValidationUtility.validate_open_ended(question_updates)

    @staticmethod
    # Utility to normalize all datetimes to UTC-aware
    def validate_utc(dt: Any):
        if dt is None:
            return None
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)  # assume naive = UTC
            return dt.astimezone(timezone.utc)
        return dt

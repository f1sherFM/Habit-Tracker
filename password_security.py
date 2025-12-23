"""
Password Security Module
Provides enhanced password validation and security features
"""

import re
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Tuple, List


class PasswordValidator:
    """
    Enhanced password validation with strength checking and security features
    """
    
    # Password strength requirements
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    # Character requirements
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True
    
    # Special characters allowed
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Common weak passwords to reject
    WEAK_PASSWORDS = {
        'password', 'password123', '123456', '123456789', 'qwerty',
        'abc123', 'password1', 'admin', 'letmein', 'welcome',
        'monkey', '1234567890', 'dragon', 'master', 'hello',
        'login', 'pass', 'admin123', 'root', 'user'
    }
    
    @classmethod
    def validate_password_strength(cls, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength against security requirements.
        
        Args:
            password: The password to validate
            
        Returns:
            Tuple of (is_valid: bool, error_messages: List[str])
        """
        errors = []
        
        # Check length requirements
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")
        
        if len(password) > cls.MAX_LENGTH:
            errors.append(f"Password must be no more than {cls.MAX_LENGTH} characters long")
        
        # Check character requirements
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if cls.REQUIRE_DIGITS and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if cls.REQUIRE_SPECIAL and not re.search(f'[{re.escape(cls.SPECIAL_CHARS)}]', password):
            errors.append(f"Password must contain at least one special character ({cls.SPECIAL_CHARS})")
        
        # Check for weak passwords
        if password.lower() in cls.WEAK_PASSWORDS:
            errors.append("Password is too common and easily guessable")
        
        # Check for repeated characters (more than 3 in a row)
        if re.search(r'(.)\1{3,}', password):
            errors.append("Password cannot contain more than 3 repeated characters in a row")
        
        # Check for sequential characters (like 123 or abc)
        if cls._has_sequential_chars(password):
            errors.append("Password cannot contain sequential characters (like 123 or abc)")
        
        return len(errors) == 0, errors
    
    @classmethod
    def _has_sequential_chars(cls, password: str) -> bool:
        """
        Check if password contains sequential characters.
        
        Args:
            password: The password to check
            
        Returns:
            bool: True if sequential characters found
        """
        password_lower = password.lower()
        
        # Check for sequential numbers (123, 234, etc.)
        for i in range(len(password_lower) - 2):
            if (password_lower[i].isdigit() and 
                password_lower[i+1].isdigit() and 
                password_lower[i+2].isdigit()):
                if (ord(password_lower[i+1]) == ord(password_lower[i]) + 1 and
                    ord(password_lower[i+2]) == ord(password_lower[i+1]) + 1):
                    return True
        
        # Check for sequential letters (abc, def, etc.)
        for i in range(len(password_lower) - 2):
            if (password_lower[i].isalpha() and 
                password_lower[i+1].isalpha() and 
                password_lower[i+2].isalpha()):
                if (ord(password_lower[i+1]) == ord(password_lower[i]) + 1 and
                    ord(password_lower[i+2]) == ord(password_lower[i+1]) + 1):
                    return True
        
        return False
    
    @classmethod
    def calculate_password_strength(cls, password: str) -> Tuple[int, str]:
        """
        Calculate password strength score and description.
        
        Args:
            password: The password to evaluate
            
        Returns:
            Tuple of (score: int (0-100), description: str)
        """
        score = 0
        
        # Length scoring (up to 25 points)
        if len(password) >= 8:
            score += min(25, len(password) * 2)
        
        # Character variety scoring (up to 40 points)
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'\d', password):
            score += 10
        if re.search(f'[{re.escape(cls.SPECIAL_CHARS)}]', password):
            score += 10
        
        # Complexity bonus (up to 35 points)
        unique_chars = len(set(password))
        score += min(15, unique_chars)
        
        # No repeated patterns
        if not re.search(r'(.)\1{2,}', password):
            score += 10
        
        # No sequential characters
        if not cls._has_sequential_chars(password):
            score += 10
        
        # Determine strength description
        if score >= 80:
            description = "Very Strong"
        elif score >= 60:
            description = "Strong"
        elif score >= 40:
            description = "Moderate"
        elif score >= 20:
            description = "Weak"
        else:
            description = "Very Weak"
        
        return min(100, score), description


class SecurePasswordHasher:
    """
    Enhanced password hashing with configurable security parameters
    """
    
    # Default hashing method - using pbkdf2:sha256 with high iterations
    DEFAULT_METHOD = 'pbkdf2:sha256:260000'  # 260,000 iterations for strong security
    
    @classmethod
    def hash_password(cls, password: str, method: str = None) -> str:
        """
        Hash a password using secure methods.
        
        Args:
            password: The plain text password to hash
            method: The hashing method to use (defaults to DEFAULT_METHOD)
            
        Returns:
            str: The hashed password
        """
        if method is None:
            method = cls.DEFAULT_METHOD
        
        return generate_password_hash(password, method=method)
    
    @classmethod
    def verify_password(cls, password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: The plain text password to verify
            password_hash: The stored password hash
            
        Returns:
            bool: True if password matches hash
        """
        return check_password_hash(password_hash, password)
    
    @classmethod
    def needs_rehash(cls, password_hash: str) -> bool:
        """
        Check if a password hash needs to be updated to current security standards.
        
        Args:
            password_hash: The stored password hash
            
        Returns:
            bool: True if hash should be updated
        """
        # Check if hash uses old method or insufficient iterations
        if not password_hash.startswith('pbkdf2:sha256:'):
            return True
        
        # Extract iteration count
        try:
            parts = password_hash.split(':')
            if len(parts) >= 3:
                iterations = int(parts[2])
                # Require at least 200,000 iterations
                return iterations < 200000
        except (ValueError, IndexError):
            return True
        
        return False
    
    @classmethod
    def generate_secure_token(cls, length: int = 32) -> str:
        """
        Generate a cryptographically secure random token.
        
        Args:
            length: The length of the token in bytes
            
        Returns:
            str: A secure random token
        """
        return secrets.token_urlsafe(length)


def validate_and_hash_password(password: str, confirm_password: str = None) -> Tuple[bool, str, str]:
    """
    Convenience function to validate and hash a password.
    
    Args:
        password: The password to validate and hash
        confirm_password: Optional password confirmation
        
    Returns:
        Tuple of (success: bool, message: str, hashed_password: str)
    """
    # Check password confirmation if provided
    if confirm_password is not None and password != confirm_password:
        return False, "Passwords do not match", ""
    
    # Validate password strength
    is_valid, errors = PasswordValidator.validate_password_strength(password)
    
    if not is_valid:
        return False, "; ".join(errors), ""
    
    # Hash the password
    try:
        hashed_password = SecurePasswordHasher.hash_password(password)
        return True, "Password is valid and secure", hashed_password
    except Exception as e:
        return False, f"Error hashing password: {str(e)}", ""
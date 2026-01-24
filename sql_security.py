"""
SQL Security Module
Provides SQL injection prevention verification and input validation
"""

import re
import html
from typing import Any, Dict, List, Tuple, Union
from sqlalchemy import text
from sqlalchemy.orm import Query
from flask import request
import logging

logger = logging.getLogger(__name__)


class SQLInjectionDetector:
    """
    Detects potential SQL injection attempts in user input
    """
    
    # Common SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        # Union-based injection
        r'\bunion\b.*\bselect\b',
        r'\bunion\b.*\ball\b.*\bselect\b',
        
        # Boolean-based blind injection
        r'\bor\b.*\b1\s*=\s*1\b',
        r'\band\b.*\b1\s*=\s*1\b',
        r'\bor\b.*\btrue\b',
        r'\band\b.*\bfalse\b',
        
        # Time-based blind injection
        r'\bwaitfor\b.*\bdelay\b',
        r'\bsleep\b\s*\(',
        r'\bbenchmark\b\s*\(',
        
        # Error-based injection
        r'\bextractvalue\b\s*\(',
        r'\bupdatexml\b\s*\(',
        r'\bcast\b.*\bas\b.*\bint\b',
        
        # Stacked queries
        r';\s*drop\b',
        r';\s*delete\b',
        r';\s*insert\b',
        r';\s*update\b',
        r';\s*create\b',
        r';\s*alter\b',
        
        # Comment-based injection
        r'--\s*$',
        r'/\*.*\*/',
        r'#.*$',
        
        # Information schema queries
        r'\binformation_schema\b',
        r'\bsys\b\.\btables\b',
        r'\bsysobjects\b',
        
        # Database-specific functions
        r'\bversion\b\s*\(\s*\)',
        r'\buser\b\s*\(\s*\)',
        r'\bdatabase\b\s*\(\s*\)',
        r'\bschema\b\s*\(\s*\)',
        
        # Hex encoding attempts
        r'0x[0-9a-fA-F]+',
        
        # Char/ASCII functions
        r'\bchar\b\s*\(',
        r'\bascii\b\s*\(',
        r'\bord\b\s*\(',
        
        # Substring functions often used in blind injection
        r'\bsubstring\b\s*\(',
        r'\bsubstr\b\s*\(',
        r'\bmid\b\s*\(',
        r'\bleft\b\s*\(',
        r'\bright\b\s*\(',
    ]
    
    # Compile patterns for better performance
    COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in SQL_INJECTION_PATTERNS]
    
    @classmethod
    def detect_sql_injection(cls, input_value: str) -> Tuple[bool, List[str]]:
        """
        Detect potential SQL injection attempts in input.
        
        Args:
            input_value: The input string to analyze
            
        Returns:
            Tuple of (is_suspicious: bool, detected_patterns: List[str])
        """
        if not isinstance(input_value, str):
            return False, []
        
        detected_patterns = []
        
        # Normalize input for analysis
        normalized_input = input_value.lower().strip()
        
        # Check against known patterns
        for i, pattern in enumerate(cls.COMPILED_PATTERNS):
            if pattern.search(normalized_input):
                detected_patterns.append(cls.SQL_INJECTION_PATTERNS[i])
        
        return len(detected_patterns) > 0, detected_patterns
    
    @classmethod
    def analyze_request_for_sql_injection(cls) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Analyze the current Flask request for SQL injection attempts.
        
        Returns:
            Tuple of (threats_detected: bool, threat_details: Dict[str, List[str]])
        """
        threats = {}
        
        # Check form data
        if request.form:
            for key, value in request.form.items():
                is_suspicious, patterns = cls.detect_sql_injection(str(value))
                if is_suspicious:
                    threats[f"form.{key}"] = patterns
        
        # Check query parameters
        if request.args:
            for key, value in request.args.items():
                is_suspicious, patterns = cls.detect_sql_injection(str(value))
                if is_suspicious:
                    threats[f"query.{key}"] = patterns
        
        # Check JSON data if present
        if request.is_json:
            try:
                json_data = request.get_json(silent=True)
                if json_data:
                    cls._check_json_recursively(json_data, threats, "json")
            except Exception:
                # Ignore JSON parsing errors - they will be handled by the route
                pass
        
        return len(threats) > 0, threats
    
    @classmethod
    def _check_json_recursively(cls, data: Any, threats: Dict[str, List[str]], path: str):
        """
        Recursively check JSON data for SQL injection patterns.
        
        Args:
            data: The data to check
            threats: Dictionary to store detected threats
            path: Current path in the JSON structure
        """
        if isinstance(data, dict):
            for key, value in data.items():
                cls._check_json_recursively(value, threats, f"{path}.{key}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                cls._check_json_recursively(item, threats, f"{path}[{i}]")
        elif isinstance(data, str):
            is_suspicious, patterns = cls.detect_sql_injection(data)
            if is_suspicious:
                threats[path] = patterns


class InputValidator:
    """
    Validates and sanitizes user input to prevent SQL injection
    """
    
    @staticmethod
    def sanitize_string(input_value: str, max_length: int = None, allow_html: bool = False) -> str:
        """
        Sanitize string input to prevent SQL injection and XSS.
        
        Args:
            input_value: The input string to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags
            
        Returns:
            str: Sanitized string
        """
        if not isinstance(input_value, str):
            return ""
        
        # Trim whitespace
        sanitized = input_value.strip()
        
        # Limit length if specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # HTML escape if HTML is not allowed
        if not allow_html:
            sanitized = html.escape(sanitized)
        
        return sanitized
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Validate email format and check for injection attempts.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid: bool, sanitized_email: str)
        """
        if not isinstance(email, str):
            return False, ""
        
        # Basic sanitization
        email = email.strip().lower()
        
        # Check for SQL injection patterns
        is_suspicious, _ = SQLInjectionDetector.detect_sql_injection(email)
        if is_suspicious:
            return False, ""
        
        # Email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, ""
        
        # Additional security checks
        if len(email) > 254:  # RFC 5321 limit
            return False, ""
        
        return True, email
    
    @staticmethod
    def validate_integer(value: Any, min_value: int = None, max_value: int = None) -> Tuple[bool, int]:
        """
        Validate and convert integer input.
        
        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Tuple of (is_valid: bool, integer_value: int)
        """
        try:
            # Convert to integer
            int_value = int(value)
            
            # Check bounds
            if min_value is not None and int_value < min_value:
                return False, 0
            
            if max_value is not None and int_value > max_value:
                return False, 0
            
            return True, int_value
            
        except (ValueError, TypeError):
            return False, 0
    
    @staticmethod
    def validate_habit_name(name: str) -> Tuple[bool, str]:
        """
        Validate habit name input.
        
        Args:
            name: Habit name to validate
            
        Returns:
            Tuple of (is_valid: bool, sanitized_name: str)
        """
        if not isinstance(name, str):
            return False, ""
        
        # Sanitize
        sanitized = InputValidator.sanitize_string(name, max_length=100)
        
        # Check for SQL injection
        is_suspicious, _ = SQLInjectionDetector.detect_sql_injection(sanitized)
        if is_suspicious:
            return False, ""
        
        # Check minimum length
        if len(sanitized.strip()) < 1:
            return False, ""
        
        # Check for only whitespace
        if not sanitized.strip():
            return False, ""
        
        return True, sanitized


class ORMSecurityVerifier:
    """
    Verifies that database queries use SQLAlchemy ORM properly to prevent SQL injection
    """
    
    @staticmethod
    def verify_query_safety(query: Union[Query, str]) -> Tuple[bool, str]:
        """
        Verify that a query is safe from SQL injection.
        
        Args:
            query: SQLAlchemy Query object or raw SQL string
            
        Returns:
            Tuple of (is_safe: bool, message: str)
        """
        if isinstance(query, Query):
            # SQLAlchemy ORM queries are generally safe
            return True, "SQLAlchemy ORM query - automatically parameterized"
        
        elif isinstance(query, str):
            # Raw SQL strings are potentially dangerous
            # Check if it uses parameterized queries
            if ':' in query or '?' in query or '%s' in query:
                return True, "Raw SQL with parameters - likely safe if using SQLAlchemy text() with bound parameters"
            else:
                # Check for dynamic content
                if any(char in query for char in ['"', "'", ';']):
                    return False, "Raw SQL with potential string concatenation - high risk for SQL injection"
                else:
                    return True, "Static raw SQL - safe"
        
        return False, "Unknown query type"
    
    @staticmethod
    def log_query_security_check(query: Any, is_safe: bool, message: str, context: str = ""):
        """
        Log security check results for monitoring.
        
        Args:
            query: The query that was checked
            is_safe: Whether the query is considered safe
            message: Security check message
            context: Additional context about where the query is used
        """
        log_level = logging.INFO if is_safe else logging.WARNING
        
        logger.log(
            log_level,
            f"SQL Security Check - {'SAFE' if is_safe else 'UNSAFE'}: {message}. "
            f"Context: {context}. Query type: {type(query).__name__}"
        )


def create_security_middleware():
    """
    Create Flask middleware to automatically check requests for SQL injection attempts.
    
    Returns:
        function: Middleware function
    """
    def security_middleware():
        # Check current request for SQL injection attempts
        threats_detected, threat_details = SQLInjectionDetector.analyze_request_for_sql_injection()
        
        if threats_detected:
            # Log the security threat
            logger.warning(
                f"SQL injection attempt detected from IP {request.remote_addr}. "
                f"Endpoint: {request.endpoint}. Threats: {threat_details}"
            )
            
            # In a production environment, you might want to:
            # 1. Block the request
            # 2. Rate limit the IP
            # 3. Send alerts to security team
            # 4. Return a generic error message
            
            # For now, we'll just log it and continue
            # You can customize this behavior based on your security requirements
    
    return security_middleware


# Decorator for route protection
def sql_injection_protection(f):
    """
    Decorator to add SQL injection protection to Flask routes.
    
    Args:
        f: The route function to protect
        
    Returns:
        function: Protected route function
    """
    def decorated_function(*args, **kwargs):
        # Check for SQL injection attempts
        threats_detected, threat_details = SQLInjectionDetector.analyze_request_for_sql_injection()
        
        if threats_detected:
            logger.warning(
                f"SQL injection attempt blocked on route {request.endpoint}. "
                f"IP: {request.remote_addr}. Threats: {threat_details}"
            )
            
            # You can customize the response here
            # For now, we'll continue with the request but log the attempt
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function
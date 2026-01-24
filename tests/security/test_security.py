"""
Security Tests for Habit Tracker

Tests protection against SQL injection, input validation, authentication, authorization, and CORS security
"""
import pytest
import os
import json
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.models import get_models
from app.models.habit_types import HabitType
from app.services.habit_service import HabitService
from app.services.user_service import UserService
from app.exceptions import ValidationError, AuthorizationError


class TestSecurity:
    """Security tests for the Habit Tracker system"""
    
    @pytest.fixture
    def app(self):
        """Create test application with security configuration"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-for-security-tests-that-is-long-enough',
            'FLASK_ENV': 'testing',
            'DATABASE_URL': 'sqlite:///:memory:',
            'CORS_ORIGINS': 'https://trusted-domain.com',
            'CORS_METHODS': 'GET,POST,PUT,DELETE',
            'CORS_HEADERS': 'Content-Type,Authorization'
        }):
            app = create_app('testing')
            with app.app_context():
                db.create_all()
                yield app
                db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def models(self, app):
        """Get model classes"""
        return get_models()
    
    @pytest.fixture
    def services(self, app, models):
        """Create service instances"""
        User, Habit, HabitLog = models
        
        from app.validators.habit_validator import HabitValidator
        from app.validators.time_validator import TimeValidator
        from app.validators.frequency_validator import FrequencyValidator
        
        # Create validators
        time_validator = TimeValidator()
        frequency_validator = FrequencyValidator()
        habit_validator = HabitValidator(time_validator, frequency_validator)
        
        # Create services
        habit_service = HabitService(habit_validator)
        user_service = UserService()
        
        return {
            'habit_service': habit_service,
            'user_service': user_service
        }
    
    @pytest.fixture
    def test_user(self, app, models, services):
        """Create a test user"""
        User, Habit, HabitLog = models
        user_service = services['user_service']
        
        user = user_service.create_user(
            email='security@example.com',
            password='SecurePassword9!@#$%',
            name='Security Test User'
        )
        db.session.commit()
        return user
    
    def test_sql_injection_protection_in_habit_queries(self, app, models, services, test_user):
        """Test protection against SQL injection in habit queries"""
        User, Habit, HabitLog = models
        habit_service = services['habit_service']
        
        # Create a legitimate habit first
        legitimate_habit_data = {
            'name': 'Legitimate Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        habit = habit_service.create_habit(test_user.id, legitimate_habit_data)
        initial_habit_count = len(habit_service.get_user_habits(test_user.id))
        
        # Test SQL injection attempts in various fields
        sql_injection_payloads = [
            "'; DROP TABLE habits; --",
            "' OR '1'='1",
            "'; UPDATE habits SET name='HACKED'; --",
            "' UNION SELECT * FROM users; --",
            "'; INSERT INTO habits (name) VALUES ('injected'); --"
        ]
        
        successful_creations = 0
        
        for payload in sql_injection_payloads:
            # Test injection in habit name
            malicious_habit_data = {
                'name': payload,
                'execution_time': 60,
                'frequency': 7,
                'habit_type': HabitType.USEFUL
            }
            
            try:
                # Should either create habit with escaped data or fail validation
                created_habit = habit_service.create_habit(test_user.id, malicious_habit_data)
                # If created, the name should be the literal string, not executed SQL
                assert created_habit.name == payload
                successful_creations += 1
                
            except ValidationError:
                # Validation rejection is also acceptable
                pass
            
            # Verify original data is intact (no SQL injection occurred)
            original_habit = habit_service.get_habit_by_id(habit.id, test_user.id)
            assert original_habit.name == 'Legitimate Habit'
            
            # Verify no unauthorized habits were created beyond the expected ones
            user_habits = habit_service.get_user_habits(test_user.id)
            expected_count = initial_habit_count + successful_creations
            assert len(user_habits) == expected_count
            assert any(h.name == 'Legitimate Habit' for h in user_habits)
        
        # Most importantly: verify that the database structure is intact
        # and no SQL injection actually executed
        all_habits = habit_service.get_user_habits(test_user.id)
        
        # Check that no habits have names indicating successful injection
        for habit in all_habits:
            assert habit.name != 'HACKED'
            assert habit.name != 'injected'
        
        # Verify the original habit still exists with correct data
        original_habit = habit_service.get_habit_by_id(habit.id, test_user.id)
        assert original_habit.name == 'Legitimate Habit'
    
    def test_sql_injection_protection_in_user_queries(self, app, models, services):
        """Test protection against SQL injection in user queries"""
        user_service = services['user_service']
        
        # Test SQL injection in user creation
        sql_injection_payloads = [
            "test'; DROP TABLE users; --@example.com",
            "test' OR '1'='1@example.com",
            "admin@example.com'; UPDATE users SET email='hacked@evil.com'; --"
        ]
        
        for payload in sql_injection_payloads:
            try:
                # Should either create user with escaped email or fail validation
                user = user_service.create_user(
                    email=payload,
                    password='SecurePassword9!@#$%',
                    name='Test User'
                )
                # If created, the email should be the literal string
                assert user.email == payload.lower().strip()
                
            except Exception:
                # Any kind of rejection is acceptable for malformed emails
                pass
        
        # Verify no unauthorized modifications occurred
        # The database should still be in a consistent state
        try:
            # This should work normally
            legitimate_user = user_service.create_user(
                email='legitimate@example.com',
                password='SecurePassword9!@#$%',
                name='Legitimate User'
            )
            assert legitimate_user.email == 'legitimate@example.com'
        except Exception as e:
            pytest.fail(f"Legitimate user creation failed after injection attempts: {e}")
    
    def test_input_validation_and_sanitization(self, app, models, services, test_user):
        """Test input validation and sanitization across the system"""
        habit_service = services['habit_service']
        
        # Test various malicious inputs
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "'; DROP TABLE habits; --",
            "../../../etc/passwd",
            "{{7*7}}",  # Template injection
            "${7*7}",   # Expression injection
            "eval('alert(1)')",
            "<iframe src='javascript:alert(1)'></iframe>"
        ]
        
        for malicious_input in malicious_inputs:
            habit_data = {
                'name': malicious_input,
                'description': malicious_input,
                'execution_time': 60,
                'frequency': 7,
                'habit_type': HabitType.USEFUL,
                'reward': malicious_input
            }
            
            try:
                habit = habit_service.create_habit(test_user.id, habit_data)
                
                # If creation succeeded, verify data is stored as literal strings
                # (not executed as code)
                assert habit.name == malicious_input
                assert habit.description == malicious_input
                assert habit.reward == malicious_input
                
                # Verify no code execution occurred by checking system state
                # The habit should exist normally in the database
                retrieved_habit = habit_service.get_habit_by_id(habit.id, test_user.id)
                assert retrieved_habit.name == malicious_input
                
            except ValidationError:
                # Validation rejection is acceptable for malicious inputs
                pass
    
    def test_authentication_and_authorization(self, app, models, services):
        """Test authentication and authorization mechanisms"""
        User, Habit, HabitLog = models
        user_service = services['user_service']
        habit_service = services['habit_service']
        
        # Create two users
        user1 = user_service.create_user(
            email='user1@example.com',
            password='SecurePassword1!@#$%',
            name='User 1'
        )
        
        user2 = user_service.create_user(
            email='user2@example.com',
            password='SecurePassword2!@#$%',
            name='User 2'
        )
        
        # Create a habit for user1
        habit_data = {
            'name': 'User 1 Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        user1_habit = habit_service.create_habit(user1.id, habit_data)
        
        # Test authorization: user2 should not be able to access user1's habit
        with pytest.raises(AuthorizationError):
            habit_service.get_habit_by_id(user1_habit.id, user2.id)
        
        with pytest.raises(AuthorizationError):
            habit_service.update_habit(user1_habit.id, user2.id, {'name': 'Hacked'})
        
        with pytest.raises(AuthorizationError):
            habit_service.delete_habit(user1_habit.id, user2.id)
        
        # Test that user1 can still access their own habit
        retrieved_habit = habit_service.get_habit_by_id(user1_habit.id, user1.id)
        assert retrieved_habit.name == 'User 1 Habit'
        
        # Test that user2 cannot see user1's habits in their list
        user2_habits = habit_service.get_user_habits(user2.id)
        assert len(user2_habits) == 0
        
        user1_habits = habit_service.get_user_habits(user1.id)
        assert len(user1_habits) == 1
        assert user1_habits[0].name == 'User 1 Habit'
    
    def test_password_security(self, app, models, services):
        """Test password security mechanisms"""
        user_service = services['user_service']
        
        # Test password strength requirements
        weak_passwords = [
            'password',      # Too common
            '12345678',      # Sequential numbers
            'abcdefgh',      # Sequential letters
            'Password',      # Missing special chars and numbers
            'Pass123',       # Too short
            'PASSWORD123!',  # No lowercase
            'password123!',  # No uppercase
            'Password!',     # No numbers
            'Password123'    # No special chars
        ]
        
        for weak_password in weak_passwords:
            with pytest.raises(Exception):  # Should raise some validation error
                user_service.create_user(
                    email=f'test_{weak_password}@example.com',
                    password=weak_password,
                    name='Test User'
                )
        
        # Test that strong password works
        strong_password = 'StrongPassword9!@#$%'
        user = user_service.create_user(
            email='strong@example.com',
            password=strong_password,
            name='Strong User'
        )
        
        assert user is not None
        assert user.email == 'strong@example.com'
        
        # Test password authentication
        authenticated_user = user_service.authenticate_user('strong@example.com', strong_password)
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        
        # Test wrong password
        with pytest.raises(Exception):  # Should raise authentication error
            user_service.authenticate_user('strong@example.com', 'WrongPassword')
    
    def test_cors_security_configuration(self, app, client):
        """Test CORS security configuration"""
        
        # Test that CORS is properly configured with security in mind
        with app.app_context():
            cors_origins = app.config.get('CORS_ORIGINS', [])
            
            # Should not allow all origins in production-like config
            # Check for testing environment using TESTING config or FLASK_ENV
            is_testing = app.config.get('TESTING', False) or app.config.get('FLASK_ENV') == 'testing'
            
            if isinstance(cors_origins, list):
                assert '*' not in cors_origins or is_testing, f"CORS allows all origins (*) in non-testing environment. TESTING={app.config.get('TESTING')}, FLASK_ENV={app.config.get('FLASK_ENV')}"
        
        # Test preflight request with allowed origin
        headers = {
            'Origin': 'https://trusted-domain.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = client.options('/api/habits', headers=headers)
        assert response.status_code in [200, 204]
        
        # Test request with disallowed origin (if CORS is restrictive)
        malicious_headers = {
            'Origin': 'https://malicious-domain.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = client.options('/api/habits', headers=malicious_headers)
        # Response should either reject or not include CORS headers for malicious origin
        # The exact behavior depends on CORS configuration
        
        # Test that security headers are present
        response = client.get('/')
        
        # Check for important security headers
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
        
        assert 'X-XSS-Protection' in response.headers
        assert response.headers['X-XSS-Protection'] == '1; mode=block'
    
    def test_data_exposure_prevention(self, app, models, services, test_user):
        """Test prevention of sensitive data exposure"""
        User, Habit, HabitLog = models
        habit_service = services['habit_service']
        
        # Create habits with potentially sensitive information
        sensitive_habit_data = {
            'name': 'Personal Medical Information',
            'description': 'Take medication for condition XYZ',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL,
            'reward': 'Feel better about health'
        }
        
        habit = habit_service.create_habit(test_user.id, sensitive_habit_data)
        
        # Test that user can access their own data
        retrieved_habit = habit_service.get_habit_by_id(habit.id, test_user.id)
        assert retrieved_habit.description == 'Take medication for condition XYZ'
        
        # Create another user
        from app.services.user_service import UserService
        user_service = UserService()
        other_user = user_service.create_user(
            email='other@example.com',
            password='OtherPassword9!@#$%',
            name='Other User'
        )
        
        # Test that other user cannot access sensitive data
        with pytest.raises(AuthorizationError):
            habit_service.get_habit_by_id(habit.id, other_user.id)
        
        # Test that user lists don't leak data between users
        other_user_habits = habit_service.get_user_habits(other_user.id)
        assert len(other_user_habits) == 0
        
        # Verify no sensitive data in error messages or logs
        try:
            habit_service.get_habit_by_id(habit.id, other_user.id)
        except AuthorizationError as e:
            # Error message should not contain sensitive habit data
            error_message = str(e)
            assert 'medication' not in error_message.lower()
            assert 'condition xyz' not in error_message.lower()
    
    def test_session_security(self, app, client):
        """Test session security mechanisms"""
        
        # Test that session cookies have security flags (if sessions are used)
        response = client.get('/')
        
        # Check for secure session configuration
        if 'Set-Cookie' in response.headers:
            cookie_header = response.headers['Set-Cookie']
            # In production, should have Secure and HttpOnly flags
            # In testing, we just verify the structure is reasonable
            assert 'session' in cookie_header.lower() or 'csrf' in cookie_header.lower()
    
    def test_rate_limiting_protection(self, app, models, services, test_user):
        """Test protection against brute force and DoS attacks"""
        habit_service = services['habit_service']
        
        # Test that system can handle multiple rapid requests without crashing
        # This is a basic test - in production you'd want proper rate limiting
        
        habit_data = {
            'name': 'Rate Limit Test',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        # Make multiple rapid requests
        created_habits = []
        for i in range(10):
            try:
                habit_data['name'] = f'Rate Limit Test {i}'
                habit = habit_service.create_habit(test_user.id, habit_data)
                created_habits.append(habit)
            except Exception:
                # Some failures are acceptable under load
                pass
        
        # System should still be functional
        assert len(created_habits) > 0
        
        # Verify data integrity
        for habit in created_habits:
            retrieved = habit_service.get_habit_by_id(habit.id, test_user.id)
            assert retrieved.name.startswith('Rate Limit Test')
    
    def test_error_handling_security(self, app, models, services, test_user):
        """Test that error handling doesn't leak sensitive information"""
        habit_service = services['habit_service']
        
        # Test error handling for non-existent resources
        try:
            habit_service.get_habit_by_id(99999, test_user.id)
        except Exception as e:
            error_message = str(e)
            # Error should not reveal internal system details
            assert 'database' not in error_message.lower()
            assert 'sql' not in error_message.lower()
            assert 'table' not in error_message.lower()
            assert 'column' not in error_message.lower()
        
        # Test error handling for invalid data
        try:
            habit_service.create_habit(test_user.id, {'invalid': 'data'})
        except Exception as e:
            error_message = str(e)
            # Error should be user-friendly, not revealing internal structure
            assert 'traceback' not in error_message.lower()
            assert 'exception' not in error_message.lower()
    
    def test_input_length_limits(self, app, models, services, test_user):
        """Test protection against buffer overflow and DoS via large inputs"""
        habit_service = services['habit_service']
        
        # Test extremely long inputs
        very_long_string = 'A' * 10000
        
        habit_data = {
            'name': very_long_string,
            'description': very_long_string,
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL,
            'reward': very_long_string
        }
        
        try:
            habit = habit_service.create_habit(test_user.id, habit_data)
            # If creation succeeded, verify data is properly truncated or handled
            assert len(habit.name) <= 1000  # Reasonable limit
            assert len(habit.description) <= 5000  # Reasonable limit
            
        except ValidationError:
            # Rejection of overly long inputs is acceptable
            pass
        
        # System should still be functional after handling large input
        normal_habit_data = {
            'name': 'Normal Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        normal_habit = habit_service.create_habit(test_user.id, normal_habit_data)
        assert normal_habit.name == 'Normal Habit'
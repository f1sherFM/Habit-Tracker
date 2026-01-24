"""
Property-Based Tests for CORS Configuration

Tests universal properties of CORS system
"""
import pytest
from hypothesis import given, strategies as st
import sys
import os
from unittest.mock import patch

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.utils.cors_config import CORSConfig
from app import create_app


class TestCORSProperties:
    """Property-based tests for CORS configuration system"""
    
    @given(st.lists(
        st.one_of(
            st.just('http://localhost:3000'),
            st.just('https://example.com'),
            st.just('https://app.domain.com'),
            st.just('http://127.0.0.1:8080')
        ),
        min_size=1,
        max_size=5
    ))
    def test_cors_origins_parsing_property(self, origins_list):
        """
        Feature: habit-tracker-improvements, Property 8: CORS заголовки для API эндпоинтов
        Для любого списка валидных CORS origins система должна корректно их парсить
        Validates: Requirements 5.1, 5.3
        """
        # Create comma-separated origins string
        origins_string = ','.join(origins_list)
        
        with patch.dict(os.environ, {'CORS_ORIGINS': origins_string}):
            parsed_origins = CORSConfig.get_cors_origins()
            
            # Property: All provided origins should be parsed correctly
            assert len(parsed_origins) == len(origins_list)
            for origin in origins_list:
                assert origin in parsed_origins
    
    @given(st.lists(
        st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']),
        min_size=1,
        max_size=6,
        unique=True
    ))
    def test_cors_methods_parsing_property(self, methods_list):
        """
        Feature: habit-tracker-improvements, Property 8: CORS заголовки для API эндпоинтов
        Для любого списка валидных HTTP методов система должна корректно их парсить
        Validates: Requirements 5.4
        """
        # Create comma-separated methods string
        methods_string = ','.join(methods_list)
        
        with patch.dict(os.environ, {'CORS_METHODS': methods_string}):
            parsed_methods = CORSConfig.get_cors_methods()
            
            # Property: All provided methods should be parsed correctly
            assert len(parsed_methods) == len(methods_list)
            for method in methods_list:
                assert method in parsed_methods
    
    @given(st.lists(
        st.sampled_from(['Content-Type', 'Authorization', 'X-Requested-With', 'Accept', 'Origin']),
        min_size=1,
        max_size=5,
        unique=True
    ))
    def test_cors_headers_parsing_property(self, headers_list):
        """
        Feature: habit-tracker-improvements, Property 8: CORS заголовки для API эндпоинтов
        Для любого списка валидных заголовков система должна корректно их парсить
        Validates: Requirements 5.5
        """
        # Create comma-separated headers string
        headers_string = ','.join(headers_list)
        
        with patch.dict(os.environ, {'CORS_HEADERS': headers_string}):
            parsed_headers = CORSConfig.get_cors_headers()
            
            # Property: All provided headers should be parsed correctly
            assert len(parsed_headers) == len(headers_list)
            for header in headers_list:
                assert header in parsed_headers
    
    @given(st.one_of(
        st.just('http://localhost:3000'),
        st.just('https://example.com'),
        st.just('https://app.domain.com')
    ))
    def test_origin_validation_with_allowed_origins(self, test_origin):
        """
        Feature: habit-tracker-improvements, Property 8: CORS заголовки для API эндпоинтов
        Для любого origin из списка разрешенных система должна разрешить доступ
        Validates: Requirements 5.3
        """
        allowed_origins = [
            'http://localhost:3000',
            'https://example.com', 
            'https://app.domain.com'
        ]
        origins_string = ','.join(allowed_origins)
        
        with patch.dict(os.environ, {'CORS_ORIGINS': origins_string}):
            is_valid = CORSConfig.validate_origin(test_origin)
            
            # Property: Any origin in allowed list should be valid
            assert is_valid is True
    
    @given(st.one_of(
        st.just('http://malicious.com'),
        st.just('https://evil.org'),
        st.just('http://unauthorized.net')
    ))
    def test_origin_validation_with_disallowed_origins(self, test_origin):
        """
        Feature: habit-tracker-improvements, Property 8: CORS заголовки для API эндпоинтов
        Для любого origin не из списка разрешенных система должна запретить доступ
        Validates: Requirements 5.3
        """
        allowed_origins = [
            'http://localhost:3000',
            'https://example.com'
        ]
        origins_string = ','.join(allowed_origins)
        
        with patch.dict(os.environ, {'CORS_ORIGINS': origins_string}):
            is_valid = CORSConfig.validate_origin(test_origin)
            
            # Property: Any origin not in allowed list should be invalid
            assert is_valid is False
    
    @given(st.integers(min_value=0, max_value=86400))
    def test_cors_max_age_parsing_property(self, max_age_value):
        """
        Feature: habit-tracker-improvements, Property 8: CORS заголовки для API эндпоинтов
        Для любого валидного значения max_age система должна корректно его парсить
        Validates: Requirements 5.4
        """
        with patch.dict(os.environ, {'CORS_MAX_AGE': str(max_age_value)}):
            parsed_max_age = CORSConfig.get_cors_max_age()
            
            # Property: Valid max_age values should be parsed correctly
            assert parsed_max_age == max_age_value
            assert isinstance(parsed_max_age, int)
    
    @given(st.sampled_from(['true', 'false', 'True', 'False', 'TRUE', 'FALSE']))
    def test_cors_credentials_parsing_property(self, credentials_value):
        """
        Feature: habit-tracker-improvements, Property 8: CORS заголовки для API эндпоинтов
        Для любого валидного значения credentials система должна корректно его парсить
        Validates: Requirements 5.4
        """
        with patch.dict(os.environ, {'CORS_CREDENTIALS': credentials_value}):
            parsed_credentials = CORSConfig.get_cors_credentials()
            
            # Property: Credentials should be parsed as boolean
            expected_value = credentials_value.lower() == 'true'
            assert parsed_credentials == expected_value
            assert isinstance(parsed_credentials, bool)
    
    def test_wildcard_origin_allows_all_property(self):
        """
        Feature: habit-tracker-improvements, Property 8: CORS заголовки для API эндпоинтов
        Когда CORS_ORIGINS установлен в '*', система должна разрешить любой origin
        Validates: Requirements 5.1, 5.3
        """
        with patch.dict(os.environ, {'CORS_ORIGINS': '*'}):
            # Test various origins
            test_origins = [
                'http://localhost:3000',
                'https://example.com',
                'https://any-domain.org',
                'http://127.0.0.1:8080'
            ]
            
            for origin in test_origins:
                is_valid = CORSConfig.validate_origin(origin)
                # Property: Wildcard should allow any origin
                assert is_valid is True
    
    @given(st.sampled_from(['true', 'false', 'True', 'False', 'TRUE', 'FALSE']))
    def test_cors_enabled_flag_property(self, enabled_value):
        """
        Feature: habit-tracker-improvements, Property 8: CORS заголовки для API эндпоинтов
        Для любого валидного значения CORS_ENABLED система должна корректно его интерпретировать
        Validates: Requirements 5.1
        """
        with patch.dict(os.environ, {'CORS_ENABLED': enabled_value}):
            is_enabled = CORSConfig.is_cors_enabled()
            
            # Property: CORS enabled flag should be parsed as boolean
            expected_value = enabled_value.lower() == 'true'
            assert is_enabled == expected_value
            assert isinstance(is_enabled, bool)
"""
Property-Based Tests for Configuration Loading

Tests universal properties of configuration system
"""
import pytest
from hypothesis import given, strategies as st
import sys
import os
from unittest.mock import patch

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.config import get_config, DevelopmentConfig, TestingConfig, ProductionConfig
from app.validators.config_validator import ConfigValidator


class TestConfigProperties:
    """Property-based tests for configuration loading system"""
    
    @given(st.text(min_size=32, max_size=128, alphabet=st.characters(min_codepoint=33, max_codepoint=126)))
    def test_config_loads_secret_key_from_environment(self, secret_key):
        """
        Feature: habit-tracker-improvements, Property 7: Загрузка конфигурации из переменных окружения
        Для любого валидного SECRET_KEY система должна загрузить его из переменных окружения
        Validates: Requirements 4.1
        """
        with patch.dict(os.environ, {'SECRET_KEY': secret_key}):
            # Import config module after setting environment to get fresh values
            import importlib
            from app import config as config_module
            importlib.reload(config_module)
            
            config_class = config_module.DevelopmentConfig
            
            # Property: Configuration should load SECRET_KEY from environment
            assert config_class.SECRET_KEY == secret_key
    
    @given(st.sampled_from([
        'sqlite:///test.db',
        'postgresql://user:pass@localhost/db',
        'postgres://user:pass@localhost:5432/db'
    ]))
    def test_config_loads_database_url_from_environment(self, database_url):
        """
        Feature: habit-tracker-improvements, Property 7: Загрузка конфигурации из переменных окружения
        Для любого валидного DATABASE_URL система должна загрузить его из переменных окружения
        Validates: Requirements 4.1
        """
        with patch.dict(os.environ, {
            'DATABASE_URL': database_url,
            'SECRET_KEY': 'a-very-long-and-secure-secret-key-for-testing-purposes'
        }):
            # Import config module after setting environment to get fresh values
            import importlib
            from app import config as config_module
            importlib.reload(config_module)
            
            config_class = config_module.ProductionConfig
            
            # Property: Configuration should load DATABASE_URL from environment
            assert config_class.SQLALCHEMY_DATABASE_URI == database_url
    
    @given(st.lists(
        st.sampled_from([
            'http://localhost:3000',
            'https://example.com',
            'https://app.domain.com'
        ]),
        min_size=1,
        max_size=3,
        unique=True
    ))
    def test_config_loads_cors_origins_from_environment(self, origins_list):
        """
        Feature: habit-tracker-improvements, Property 7: Загрузка конфигурации из переменных окружения
        Для любого списка валидных CORS origins система должна загрузить их из переменных окружения
        Validates: Requirements 4.1
        """
        origins_string = ','.join(origins_list)
        
        with patch.dict(os.environ, {'CORS_ORIGINS': origins_string}):
            # Import CORSConfig after setting environment
            from app.utils.cors_config import CORSConfig
            parsed_origins = CORSConfig.get_cors_origins()
            
            # Property: Configuration should load and parse CORS origins from environment
            assert len(parsed_origins) == len(origins_list)
            for origin in origins_list:
                assert origin in parsed_origins
    
    @given(st.sampled_from(['development', 'testing', 'production']))
    def test_config_returns_correct_class_for_environment(self, env_name):
        """
        Feature: habit-tracker-improvements, Property 7: Загрузка конфигурации из переменных окружения
        Для любого валидного имени окружения система должна вернуть соответствующий класс конфигурации
        Validates: Requirements 4.1
        """
        # Set required environment variables for production
        env_vars = {
            'SECRET_KEY': 'a-very-long-and-secure-secret-key-for-testing-purposes',
            'DATABASE_URL': 'postgresql://user:pass@localhost/db'
        }
        
        with patch.dict(os.environ, env_vars):
            config_class = get_config(env_name)
            
            # Property: Each environment should return its specific config class
            if env_name == 'development':
                assert config_class.__name__ == 'DevelopmentConfig'
            elif env_name == 'testing':
                assert config_class.__name__ == 'TestingConfig'
            elif env_name == 'production':
                assert config_class.__name__ == 'ProductionConfig'
    
    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
    def test_config_uses_default_for_unknown_environment(self, unknown_env):
        """
        Feature: habit-tracker-improvements, Property 7: Загрузка конфигурации из переменных окружения
        Для любого неизвестного имени окружения система должна использовать конфигурацию по умолчанию
        Validates: Requirements 4.1
        """
        # Ensure it's not a known environment
        if unknown_env not in ['development', 'testing', 'production']:
            config_class = get_config(unknown_env)
            
            # Property: Unknown environments should default to DevelopmentConfig
            assert config_class.__name__ == 'DevelopmentConfig'
    
    @given(st.text(min_size=32, max_size=128, alphabet=st.characters(min_codepoint=33, max_codepoint=126)))
    def test_production_config_validates_required_vars(self, secret_key):
        """
        Feature: habit-tracker-improvements, Property 7: Загрузка конфигурации из переменных окружения
        Для любой производственной конфигурации система должна проверять наличие обязательных переменных
        Validates: Requirements 4.1
        """
        database_url = 'postgresql://user:pass@localhost/db'
        
        with patch.dict(os.environ, {
            'SECRET_KEY': secret_key,
            'DATABASE_URL': database_url,
            'FLASK_ENV': 'production'
        }):
            # This should not raise an exception
            config_class = get_config('production')
            is_valid, missing_vars = config_class.validate_required_vars()
            
            # Property: Valid production config should pass validation
            assert is_valid is True
            assert len(missing_vars) == 0
    
    def test_production_config_fails_without_required_vars(self):
        """
        Feature: habit-tracker-improvements, Property 7: Загрузка конфигурации из переменных окружения
        Когда обязательные переменные отсутствуют, система должна сообщить об ошибке
        Validates: Requirements 4.1
        """
        # Clear required environment variables
        with patch.dict(os.environ, {}, clear=True):
            # This should raise an exception due to missing required vars
            with pytest.raises(EnvironmentError) as exc_info:
                get_config('production')
            
            # Property: Missing required vars should cause validation failure
            assert 'SECRET_KEY' in str(exc_info.value)
            assert 'DATABASE_URL' in str(exc_info.value)
    
    @given(st.sampled_from(['true', 'false', 'True', 'False', 'TRUE', 'FALSE']))
    def test_config_validator_parses_boolean_environment_vars(self, bool_value):
        """
        Feature: habit-tracker-improvements, Property 7: Загрузка конфигурации из переменных окружения
        Для любого валидного булевого значения система должна корректно его интерпретировать
        Validates: Requirements 4.1
        """
        with patch.dict(os.environ, {'CORS_ENABLED': bool_value}):
            from app.utils.cors_config import CORSConfig
            is_enabled = CORSConfig.is_cors_enabled()
            
            # Property: Boolean environment variables should be parsed correctly
            expected_value = bool_value.lower() == 'true'
            assert is_enabled == expected_value
            assert isinstance(is_enabled, bool)
    
    @given(st.integers(min_value=0, max_value=86400))
    def test_config_validator_parses_integer_environment_vars(self, int_value):
        """
        Feature: habit-tracker-improvements, Property 7: Загрузка конфигурации из переменных окружения
        Для любого валидного целочисленного значения система должна корректно его парсить
        Validates: Requirements 4.1
        """
        with patch.dict(os.environ, {'CORS_MAX_AGE': str(int_value)}):
            from app.utils.cors_config import CORSConfig
            max_age = CORSConfig.get_cors_max_age()
            
            # Property: Integer environment variables should be parsed correctly
            assert max_age == int_value
            assert isinstance(max_age, int)
    
    def test_config_validator_startup_validation_property(self):
        """
        Feature: habit-tracker-improvements, Property 7: Загрузка конфигурации из переменных окружения
        При запуске приложения система должна проверить все критически важные переменные окружения
        Validates: Requirements 4.1
        """
        # Test with valid configuration
        valid_config = {
            'SECRET_KEY': 'a-very-long-and-secure-secret-key-for-testing-purposes',
            'FLASK_ENV': 'development',
            'CORS_ENABLED': 'true',
            'CORS_ORIGINS': 'http://localhost:3000',
            'CORS_METHODS': 'GET,POST,PUT,DELETE,OPTIONS',
            'CORS_MAX_AGE': '3600'
        }
        
        with patch.dict(os.environ, valid_config):
            result = ConfigValidator.validate_startup_config()
            
            # Property: Valid startup configuration should pass validation
            assert result.is_valid is True
            assert len(result.errors) == 0
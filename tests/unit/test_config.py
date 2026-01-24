"""
Unit Tests for Configuration Module

Tests environment variable loading and validation
"""
import os
import pytest
from unittest.mock import patch
from app.config import get_config, DevelopmentConfig, TestingConfig, ProductionConfig
from app.validators.config_validator import ConfigValidator


class TestConfigurationLoading:
    """Test configuration loading from environment variables"""
    
    def test_development_config_loads_correctly(self):
        """Test that development configuration loads with correct defaults"""
        config = get_config('development')
        
        assert config.DEBUG is True
        assert config.TESTING is False
        assert config.SQLALCHEMY_TRACK_MODIFICATIONS is False
        assert 'sqlite://' in config.SQLALCHEMY_DATABASE_URI
    
    def test_testing_config_loads_correctly(self):
        """Test that testing configuration loads with correct settings"""
        config = get_config('testing')
        
        assert config.TESTING is True
        assert config.SQLALCHEMY_DATABASE_URI == 'sqlite:///:memory:'
        assert config.WTF_CSRF_ENABLED is False
    
    def test_production_config_loads_with_env_vars(self):
        """Test that production configuration loads with environment variables"""
        # Set environment variables before importing config
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key', 'DATABASE_URL': 'postgresql://test'}):
            # Re-import to get fresh config with new env vars
            import importlib
            from app import config as config_module
            importlib.reload(config_module)
            
            config = config_module.get_config('production')
            
            assert config.DEBUG is False
            assert config.SECRET_KEY == 'test-secret-key'
            assert config.SQLALCHEMY_DATABASE_URI == 'postgresql://test'
    
    @patch.dict(os.environ, {}, clear=True)
    def test_production_config_fails_without_required_vars(self):
        """Test that production configuration fails without required environment variables"""
        with pytest.raises(EnvironmentError) as exc_info:
            get_config('production')
        
        assert 'Missing required environment variables' in str(exc_info.value)
        assert 'SECRET_KEY' in str(exc_info.value)
    
    def test_cors_origins_parsing(self):
        """Test that CORS origins are parsed correctly from environment"""
        # Set environment variables before importing config
        with patch.dict(os.environ, {'CORS_ORIGINS': 'http://localhost:3000,https://example.com'}):
            # Re-import to get fresh config with new env vars
            import importlib
            from app import config as config_module
            importlib.reload(config_module)
            
            config = config_module.get_config('development')
            
            expected_origins = ['http://localhost:3000', 'https://example.com']
            assert config.CORS_ORIGINS == expected_origins


class TestConfigValidator:
    """Test configuration validation"""
    
    @patch.dict(os.environ, {'FLASK_ENV': 'production'}, clear=True)
    def test_validates_missing_required_vars_in_production(self):
        """Test validation fails when required variables are missing in production"""
        result = ConfigValidator.validate_environment_config()
        
        assert result.is_valid is False
        assert any('SECRET_KEY is required' in error for error in result.errors)
        assert any('DATABASE_URL is required' in error for error in result.errors)
    
    @patch.dict(os.environ, {'SECRET_KEY': 'short'})
    def test_validates_secret_key_length(self):
        """Test validation fails for short SECRET_KEY"""
        result = ConfigValidator.validate_environment_config()
        
        assert result.is_valid is False
        assert any('at least 32 characters' in error for error in result.errors)
    
    @patch.dict(os.environ, {'SECRET_KEY': 'your-secret-key-here'})
    def test_validates_default_secret_key_values(self):
        """Test validation fails for default SECRET_KEY values"""
        result = ConfigValidator.validate_environment_config()
        
        assert result.is_valid is False
        assert any('should not use default/example values' in error for error in result.errors)
    
    @patch.dict(os.environ, {'CORS_ORIGINS': 'invalid-origin,http://valid.com'})
    def test_validates_cors_origins_format(self):
        """Test validation fails for invalid CORS origin format"""
        result = ConfigValidator.validate_environment_config()
        
        assert result.is_valid is False
        assert any('Invalid CORS origin format' in error for error in result.errors)
    
    @patch.dict(os.environ, {'DATABASE_URL': 'invalid://url'})
    def test_validates_database_url_format(self):
        """Test validation fails for invalid database URL format"""
        result = ConfigValidator.validate_database_config()
        
        assert result.is_valid is False
        assert any('must start with sqlite://, postgresql://, or postgres://' in error for error in result.errors)
    
    @patch.dict(os.environ, {'GOOGLE_CLIENT_ID': 'test-id'}, clear=True)
    def test_validates_incomplete_oauth_config(self):
        """Test validation fails when OAuth config is incomplete"""
        result = ConfigValidator.validate_oauth_config()
        
        assert result.is_valid is False
        assert any('GOOGLE_CLIENT_SECRET is required' in error for error in result.errors)
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'a-very-long-and-secure-secret-key-for-testing-purposes-that-meets-requirements',
        'DATABASE_URL': 'postgresql://user:pass@localhost/db',
        'CORS_ORIGINS': 'http://localhost:3000,https://example.com'
    })
    def test_validates_complete_valid_config(self):
        """Test validation passes with complete valid configuration"""
        result = ConfigValidator.validate_all()
        
        assert result.is_valid is True
        assert len(result.errors) == 0


class TestEnvironmentBehavior:
    """Test behavior with different environment configurations"""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_development_environment_has_no_required_vars(self):
        """Test that development environment doesn't require environment variables"""
        # Should not raise an exception
        config = get_config('development')
        assert config is not None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_testing_environment_has_no_required_vars(self):
        """Test that testing environment doesn't require environment variables"""
        # Should not raise an exception
        config = get_config('testing')
        assert config is not None
    
    def test_default_config_when_no_flask_env_set(self):
        """Test that default configuration is used when FLASK_ENV is not set"""
        with patch.dict(os.environ, {}, clear=True):
            config = get_config()
            # Should default to development config
            assert config.DEBUG is True
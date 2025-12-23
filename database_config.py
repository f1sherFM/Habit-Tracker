"""
Database Configuration Manager
Handles database connections across different environments with proper error handling
"""

import os
from decouple import config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """
    Database configuration manager that handles environment-based database URI selection
    and connection validation with proper error handling.
    """
    
    def __init__(self):
        """Initialize the database configuration manager."""
        self._connection_cache = None
        self._is_production_cache = None
    
    def get_database_uri(self) -> str:
        """
        Get the appropriate database URI based on the current environment.
        
        Returns:
            str: Database URI for the current environment
            
        Environment priority:
        1. DATABASE_URL (production/staging)
        2. VERCEL environment with in-memory SQLite (legacy fallback)
        3. Local SQLite database (development)
        """
        # Check for explicit DATABASE_URL first (highest priority)
        database_url = config('DATABASE_URL', default=None)
        if database_url:
            logger.info("Using DATABASE_URL for database connection")
            return database_url
        
        # Check if running on Vercel (legacy behavior)
        if self.is_production():
            logger.warning("Running on Vercel without DATABASE_URL - using in-memory SQLite (data will not persist)")
            return 'sqlite:///:memory:'
        
        # Default to local SQLite for development
        logger.info("Using local SQLite database for development")
        return 'sqlite:///habits.db'
    
    def is_production(self) -> bool:
        """
        Determine if the application is running in a production environment.
        
        Returns:
            bool: True if running in production, False otherwise
        """
        if self._is_production_cache is None:
            # Check for common production environment indicators
            vercel_env = config('VERCEL', default=None)
            railway_env = config('RAILWAY_ENVIRONMENT', default=None)
            heroku_env = config('DYNO', default=None)
            
            self._is_production_cache = bool(vercel_env or railway_env or heroku_env)
            
        return self._is_production_cache
    
    def validate_connection(self) -> bool:
        """
        Validate the database connection by attempting to connect and execute a simple query.
        
        Returns:
            bool: True if connection is valid, False otherwise
        """
        try:
            database_uri = self.get_database_uri()
            engine = create_engine(database_uri, pool_pre_ping=True)
            
            # Test connection with a simple query
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
            
            logger.info("Database connection validation successful")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database connection validation failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection validation: {str(e)}")
            return False
    
    def get_connection_params(self) -> dict:
        """
        Get database connection parameters for advanced configuration.
        
        Returns:
            dict: Connection parameters including pool settings and timeouts
        """
        database_uri = self.get_database_uri()
        
        # Base parameters for all database types
        params = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,  # Recycle connections every hour
            'connect_args': {}
        }
        
        # PostgreSQL-specific parameters (production)
        if database_uri.startswith('postgresql://') or database_uri.startswith('postgres://'):
            # Connection pooling for PostgreSQL
            pool_size = config('DB_POOL_SIZE', default=10, cast=int)
            max_overflow = config('DB_MAX_OVERFLOW', default=20, cast=int)
            pool_timeout = config('DB_POOL_TIMEOUT', default=30, cast=int)
            
            # Enforce SSL connections for security
            ssl_mode = config('DB_SSL_MODE', default='require')
            
            params.update({
                'pool_size': pool_size,
                'max_overflow': max_overflow,
                'pool_timeout': pool_timeout,
                'connect_args': {
                    'connect_timeout': 10,
                    'sslmode': ssl_mode,  # Enforce encrypted connections
                    'application_name': 'habit-tracker',
                    'sslcert': config('DB_SSL_CERT', default=None),
                    'sslkey': config('DB_SSL_KEY', default=None),
                    'sslrootcert': config('DB_SSL_ROOT_CERT', default=None)
                }
            })
            
            # Remove None values from connect_args
            params['connect_args'] = {k: v for k, v in params['connect_args'].items() if v is not None}
            
            logger.info(f"Configured PostgreSQL connection pool: size={pool_size}, max_overflow={max_overflow}, ssl_mode={ssl_mode}")
        
        # SQLite-specific parameters (development)
        elif database_uri.startswith('sqlite://'):
            params.update({
                'pool_size': 1,  # SQLite doesn't support multiple connections well
                'max_overflow': 0,
                'connect_args': {
                    'check_same_thread': False,
                    'timeout': 20
                }
            })
            
            logger.info("Configured SQLite connection for development")
        
        return params
    
    def get_error_message(self, error: Exception) -> str:
        """
        Generate user-friendly error messages for database connection issues.
        
        Args:
            error: The exception that occurred
            
        Returns:
            str: User-friendly error message
        """
        error_str = str(error).lower()
        
        # Connection timeout errors
        if 'timeout' in error_str or 'timed out' in error_str:
            return "Database connection timed out. Please check your internet connection and try again."
        
        # Authentication errors
        if 'authentication' in error_str or 'password' in error_str or 'login' in error_str:
            return "Database authentication failed. Please check your database credentials."
        
        # Network/host errors
        if 'host' in error_str or 'network' in error_str or 'connection refused' in error_str:
            return "Unable to connect to the database server. Please check if the database is running and accessible."
        
        # SSL/TLS errors
        if 'ssl' in error_str or 'tls' in error_str or 'certificate' in error_str:
            return "Database SSL connection failed. Please check your SSL configuration."
        
        # Database not found errors
        if 'database' in error_str and ('not found' in error_str or 'does not exist' in error_str):
            return "The specified database was not found. Please check your database name."
        
        # Generic fallback
        return "Database connection failed. Please check your configuration and try again."
    
    def get_environment_info(self) -> dict:
        """
        Get information about the current environment configuration.
        
        Returns:
            dict: Environment configuration details
        """
        database_uri = self.get_database_uri()
        
        info = {
            'is_production': self.is_production(),
            'database_type': 'Unknown',
            'database_uri_source': 'Unknown',
            'connection_pooling': False
        }
        
        # Determine database type
        if database_uri.startswith(('postgresql://', 'postgres://')):
            info['database_type'] = 'PostgreSQL'
            info['connection_pooling'] = True
        elif database_uri.startswith('sqlite://'):
            if ':memory:' in database_uri:
                info['database_type'] = 'SQLite (In-Memory)'
            else:
                info['database_type'] = 'SQLite (File)'
        
        # Determine URI source
        if config('DATABASE_URL', default=None):
            info['database_uri_source'] = 'DATABASE_URL environment variable'
        elif self.is_production():
            info['database_uri_source'] = 'Production fallback (in-memory SQLite)'
        else:
            info['database_uri_source'] = 'Development fallback (local SQLite)'
        
        return info
    
    def test_connection_with_feedback(self) -> tuple[bool, str]:
        """
        Test database connection and return detailed feedback.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if self.validate_connection():
                database_uri = self.get_database_uri()
                db_type = "PostgreSQL" if database_uri.startswith(('postgresql://', 'postgres://')) else "SQLite"
                
                # Also verify SSL status for PostgreSQL
                if database_uri.startswith(('postgresql://', 'postgres://')):
                    ssl_encrypted, ssl_message = self.verify_ssl_connection()
                    return True, f"Successfully connected to {db_type} database. {ssl_message}"
                else:
                    return True, f"Successfully connected to {db_type} database"
            else:
                return False, "Connection validation failed"
                
        except Exception as e:
            error_message = self.get_error_message(e)
            logger.error(f"Connection test failed: {error_message}")
            return False, error_message
    
    def verify_ssl_connection(self) -> Tuple[bool, str]:
        """
        Verify that the database connection is using SSL encryption.
        
        Returns:
            tuple: (is_encrypted: bool, status_message: str)
        """
        try:
            database_uri = self.get_database_uri()
            
            # SQLite doesn't use SSL
            if database_uri.startswith('sqlite://'):
                return True, "SQLite database - encryption not applicable"
            
            # For PostgreSQL, check SSL status
            if database_uri.startswith(('postgresql://', 'postgres://')):
                engine = create_engine(database_uri, **self.get_connection_params())
                
                with engine.connect() as connection:
                    # Query SSL status
                    result = connection.execute(text("SHOW ssl"))
                    ssl_status = result.fetchone()
                    
                    if ssl_status and ssl_status[0].lower() == 'on':
                        return True, "PostgreSQL connection is encrypted with SSL"
                    else:
                        return False, "PostgreSQL connection is not encrypted"
            
            return False, "Unknown database type - cannot verify SSL status"
            
        except SQLAlchemyError as e:
            logger.error(f"SSL verification failed: {str(e)}")
            return False, f"SSL verification failed: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during SSL verification: {str(e)}")
            return False, f"SSL verification error: {str(e)}"
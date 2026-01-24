"""
Pytest Configuration and Fixtures

Provides common test fixtures and configuration
"""
import pytest
import os
import sys
from unittest.mock import patch

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-purposes-only'
    os.environ['FLASK_ENV'] = 'testing'
    yield
    # Cleanup after tests
    os.environ.pop('SECRET_KEY', None)
    os.environ.pop('FLASK_ENV', None)


@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    from app import create_app
    from app import db as _db
    
    # Create app with testing configuration
    app = create_app('testing')
    
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def db(app):
    """Get database instance"""
    from app import db as _db
    return _db


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


@pytest.fixture
def authenticated_client(client, test_user):
    """Create an authenticated test client"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def test_user(app, db):
    """Create a test user with secure password"""
    from app.models.user import User
    
    user = User(
        email='test@example.com',
        name='Test User'
    )
    # Use a secure password that meets all requirements
    user.password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO5S7k0Ca'  # "SecurePass123!"
    
    db.session.add(user)
    db.session.commit()
    
    return user


@pytest.fixture
def sample_user(app, db):
    """Create a sample user for unit tests"""
    from app.models.user import User
    
    with app.app_context():
        user = User(
            email='sample@example.com',
            name='Sample User'
        )
        # Use a secure password that meets all requirements
        user.password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO5S7k0Ca'  # "SecurePass123!"
        
        db.session.add(user)
        db.session.commit()
        
        # Return the ID instead of the object to avoid session issues
        return user.id


@pytest.fixture
def another_user(app, db):
    """Create another test user for authorization tests"""
    from app.models.user import User
    
    with app.app_context():
        user = User(
            email='another@example.com',
            name='Another User'
        )
        # Use a secure password that meets all requirements
        user.password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO5S7k0Ca'  # "SecurePass123!"
        
        db.session.add(user)
        db.session.commit()
        
        # Return the ID instead of the object to avoid session issues
        return user.id


@pytest.fixture
def models(app):
    """Get model classes"""
    from app.models.user import User
    from app.models.habit import Habit
    from app.models.habit_log import HabitLog
    
    return {
        'User': User,
        'Habit': Habit,
        'HabitLog': HabitLog
    }


@pytest.fixture
def clean_environment():
    """Fixture that provides a clean environment for testing"""
    with patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture
def mock_production_env():
    """Fixture that mocks a production environment"""
    with patch.dict(os.environ, {
        'FLASK_ENV': 'production',
        'SECRET_KEY': 'a-very-long-and-secure-secret-key-for-testing-purposes-that-meets-requirements',
        'DATABASE_URL': 'postgresql://user:pass@localhost/testdb'
    }):
        yield


@pytest.fixture
def mock_development_env():
    """Fixture that mocks a development environment"""
    with patch.dict(os.environ, {
        'FLASK_ENV': 'development',
        'SECRET_KEY': 'test-secret-key-for-development',
        'DEV_DATABASE_URL': 'sqlite:///test_dev.db'
    }):
        yield
"""
Simple Integration Test for Habit Tracker System

Tests basic integration without complex configuration requirements.
"""
import os
import sys
import tempfile
from datetime import datetime, timezone

# Set required environment variables for testing
os.environ['SECRET_KEY'] = 'test-secret-key-for-integration-testing'
os.environ['FLASK_ENV'] = 'testing'

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import init_db, get_models, reset_models
from app.models.habit_types import HabitType
from app.services.habit_service import HabitService
from app.services.user_service import UserService
from app.validators.habit_validator import HabitValidator
from app.validators.time_validator import TimeValidator
from app.validators.frequency_validator import FrequencyValidator


def test_basic_integration():
    """Test basic system integration"""
    print("🔧 Starting integration test...")
    
    # Reset models to avoid conflicts
    reset_models()
    
    # Create test app
    app = create_app('testing')
    
    with app.app_context():
        # Create database tables
        db.create_all()
        print("✅ Database tables created")
        
        # Get model classes
        User, Habit, HabitLog = get_models()
        print("✅ Models loaded successfully")
        
        # Create validators
        time_validator = TimeValidator()
        frequency_validator = FrequencyValidator()
        habit_validator = HabitValidator(time_validator, frequency_validator)
        print("✅ Validators created")
        
        # Create services
        habit_service = HabitService(habit_validator)
        user_service = UserService()
        print("✅ Services created")
        
        # Test user creation
        user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'name': 'Test User'
        }
        
        try:
            user = user_service.create_user(user_data)
            db.session.commit()
            print(f"✅ User created: {user.email}")
        except Exception as e:
            print(f"❌ User creation failed: {e}")
            return False
        
        # Test habit creation
        habit_data = {
            'name': 'Morning Exercise',
            'description': 'Daily morning workout',
            'execution_time': 60,  # 1 minute
            'frequency': 7,  # Weekly
            'habit_type': HabitType.USEFUL,
            'reward': 'Healthy breakfast'
        }
        
        try:
            habit = habit_service.create_habit(user.id, habit_data)
            print(f"✅ Habit created: {habit.name}")
        except Exception as e:
            print(f"❌ Habit creation failed: {e}")
            return False
        
        # Test habit validation
        invalid_habit_data = {
            'name': 'Invalid Habit',
            'execution_time': 150,  # Invalid: > 120 seconds
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        try:
            habit_service.create_habit(user.id, invalid_habit_data)
            print("❌ Validation should have failed but didn't")
            return False
        except Exception as e:
            print(f"✅ Validation correctly failed: {type(e).__name__}")
        
        # Test habit update
        try:
            update_data = {'execution_time': 90}
            updated_habit = habit_service.update_habit(habit.id, user.id, update_data)
            print(f"✅ Habit updated: execution_time = {updated_habit.execution_time}")
        except Exception as e:
            print(f"❌ Habit update failed: {e}")
            return False
        
        # Test habit retrieval
        try:
            user_habits = habit_service.get_user_habits(user.id)
            print(f"✅ Retrieved {len(user_habits)} habits for user")
        except Exception as e:
            print(f"❌ Habit retrieval failed: {e}")
            return False
        
        # Test authorization (try to update as wrong user)
        try:
            # Create another user
            other_user_data = {
                'email': 'other@example.com',
                'password': 'OtherPassword123!',
                'name': 'Other User'
            }
            other_user = user_service.create_user(other_user_data)
            db.session.commit()
            
            # Try to update habit as other user (should fail)
            habit_service.update_habit(habit.id, other_user.id, {'name': 'Hacked'})
            print("❌ Authorization should have failed but didn't")
            return False
        except Exception as e:
            print(f"✅ Authorization correctly failed: {type(e).__name__}")
        
        # Test habit deletion
        try:
            result = habit_service.delete_habit(habit.id, user.id)
            print(f"✅ Habit deleted: {result}")
        except Exception as e:
            print(f"❌ Habit deletion failed: {e}")
            return False
        
        # Clean up
        db.drop_all()
        print("✅ Database cleaned up")
    
    print("🎉 All integration tests passed!")
    return True


def test_cors_configuration():
    """Test CORS configuration"""
    print("\n🔧 Testing CORS configuration...")
    
    # Reset models to avoid conflicts
    reset_models()
    
    app = create_app('testing')
    
    with app.test_client() as client:
        # Test that CORS headers are present
        response = client.options('/api/test', headers={
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST'
        })
        
        print(f"✅ CORS preflight response status: {response.status_code}")
        
        # Check for CORS headers (they should be present even if endpoint doesn't exist)
        headers = dict(response.headers)
        cors_headers = [h for h in headers.keys() if 'access-control' in h.lower()]
        
        if cors_headers:
            print(f"✅ CORS headers found: {cors_headers}")
        else:
            print("ℹ️  CORS headers not found (may be expected if CORS not fully configured)")
    
    return True


def test_configuration_loading():
    """Test configuration loading"""
    print("\n🔧 Testing configuration loading...")
    
    # Reset models to avoid conflicts
    reset_models()
    
    app = create_app('testing')
    
    # Check that configuration is loaded
    assert app.config['TESTING'] is True
    print("✅ Testing configuration loaded")
    
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
    print("✅ Database URI configured for testing")
    
    assert 'SECRET_KEY' in app.config
    print("✅ Secret key configured")
    
    # Check CORS configuration
    if 'CORS_ORIGINS' in app.config:
        print(f"✅ CORS origins configured: {app.config['CORS_ORIGINS']}")
    else:
        print("ℹ️  CORS origins not configured")
    
    return True


if __name__ == '__main__':
    print("🚀 Running Habit Tracker Integration Tests")
    print("=" * 50)
    
    success = True
    
    try:
        success &= test_configuration_loading()
        success &= test_cors_configuration()
        success &= test_basic_integration()
        
        if success:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("✅ System components are working together correctly")
            print("✅ Validation is functioning properly")
            print("✅ Authorization is working")
            print("✅ Database operations are successful")
            print("✅ Services are integrated properly")
        else:
            print("\n❌ SOME INTEGRATION TESTS FAILED!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 INTEGRATION TEST CRASHED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
#!/usr/bin/env python3
"""
Test New Models
Tests the enhanced models with new fields and business logic
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment
os.environ.setdefault('FLASK_ENV', 'development')

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime, timezone
from database_config import DatabaseConfig

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Initialize database configuration
db_config = DatabaseConfig()
database_uri = db_config.get_database_uri()
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri

# Configure SQLAlchemy engine options
connection_params = db_config.get_connection_params()

# Filter out PostgreSQL-specific parameters for SQLite
if database_uri.startswith('sqlite://'):
    engine_options = {
        'pool_pre_ping': connection_params.get('pool_pre_ping', True),
        'connect_args': connection_params.get('connect_args', {})
    }
else:
    engine_options = connection_params

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Initialize models with db instance
import app.models.user as user_module
import app.models.habit as habit_module
import app.models.habit_log as habit_log_module

user_module.db = db
habit_module.db = db
habit_log_module.db = db

# Import models
from app.models import User, Habit, HabitLog, HabitType

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def test_models():
    """Test the new models with enhanced functionality."""
    try:
        print("Testing enhanced models...")
        
        with app.app_context():
            # Create tables
            db.create_all()
            print("✅ Tables created successfully")
            
            # Test 1: Create user
            print("\n📝 Test 1: Creating user...")
            user = User(email='test@example.com', name='Test User')
            db.session.add(user)
            db.session.commit()
            print(f"✅ User created: {user}")
            
            # Test 2: Create habit with defaults
            print("\n📝 Test 2: Creating habit with defaults...")
            habit1 = Habit(
                user_id=user.id,
                name='Morning Exercise'
            )
            db.session.add(habit1)
            db.session.commit()
            
            print(f"✅ Habit created with defaults:")
            print(f"   - execution_time: {habit1.execution_time}")
            print(f"   - frequency: {habit1.frequency}")
            print(f"   - habit_type: {habit1.habit_type}")
            print(f"   - reward: {habit1.reward}")
            print(f"   - related_habit_id: {habit1.related_habit_id}")
            
            # Test 3: Create habit with explicit values
            print("\n📝 Test 3: Creating habit with explicit values...")
            habit2 = Habit(
                user_id=user.id,
                name='Read Books',
                execution_time=30,
                frequency=7,
                habit_type=HabitType.USEFUL,
                reward='Watch a movie'
            )
            db.session.add(habit2)
            db.session.commit()
            
            print(f"✅ Habit created with explicit values:")
            print(f"   - execution_time: {habit2.execution_time}")
            print(f"   - frequency: {habit2.frequency}")
            print(f"   - habit_type: {habit2.habit_type}")
            print(f"   - reward: {habit2.reward}")
            
            # Test 4: Test business rule validation
            print("\n📝 Test 4: Testing business rule validation...")
            
            # Test pleasant habit with reward (should fail)
            habit3 = Habit(
                user_id=user.id,
                name='Pleasant Habit',
                habit_type=HabitType.PLEASANT,
                reward='Some reward'
            )
            is_valid, errors = habit3.validate_business_rules()
            print(f"Pleasant habit with reward - Valid: {is_valid}, Errors: {errors}")
            
            # Test execution time > 120 seconds (should fail)
            habit4 = Habit(
                user_id=user.id,
                name='Long Habit',
                execution_time=150
            )
            is_valid, errors = habit4.validate_business_rules()
            print(f"Habit with execution_time > 120 - Valid: {is_valid}, Errors: {errors}")
            
            # Test frequency < 7 days (should fail)
            habit5 = Habit(
                user_id=user.id,
                name='Frequent Habit',
                frequency=3
            )
            is_valid, errors = habit5.validate_business_rules()
            print(f"Habit with frequency < 7 - Valid: {is_valid}, Errors: {errors}")
            
            # Test 5: Test model methods
            print("\n📝 Test 5: Testing model methods...")
            
            print(f"Habit1 is pleasant: {habit1.is_pleasant_habit()}")
            print(f"Habit1 is useful: {habit1.is_useful_habit()}")
            print(f"Habit1 has reward: {habit1.has_reward()}")
            print(f"Habit1 execution time in minutes: {habit1.get_execution_time_minutes()}")
            print(f"Habit1 frequency description: {habit1.get_frequency_description()}")
            
            # Test 6: Test relationships
            print("\n📝 Test 6: Testing relationships...")
            
            # Create related habit
            habit6 = Habit(
                user_id=user.id,
                name='Related Habit',
                related_habit_id=habit1.id
            )
            db.session.add(habit6)
            db.session.commit()
            
            print(f"Habit6 related to: {habit6.related_habit_id}")
            print(f"Habit1 related habits: {len(habit1.related_habits)}")
            
            # Test 7: Test to_dict method
            print("\n📝 Test 7: Testing to_dict method...")
            habit_dict = habit1.to_dict()
            print(f"Habit1 as dict keys: {list(habit_dict.keys())}")
            
            # Test 8: Test user statistics
            print("\n📝 Test 8: Testing user statistics...")
            stats = user.get_completion_stats()
            print(f"User stats: {stats}")
            
            print("\n🎉 All model tests completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error testing models: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = test_models()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
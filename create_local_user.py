#!/usr/bin/env python3
"""
Create a test user for local development
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set default SECRET_KEY if not set
if not os.getenv('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# Import after setting environment
sys.path.append('.')
from app import create_app, db

def create_test_user():
    """Create a test user"""
    app = create_app('development')
    
    with app.app_context():
        try:
            # Import models after app context is created
            from app.models import get_models
            User, Habit, HabitLog = get_models()
            
            # Check if user exists
            existing_user = User.query.filter_by(email='test@example.com').first()
            if existing_user:
                print('✅ Test user already exists')
                print(f'📧 Email: test@example.com')
                print(f'🔑 Password: TestPassword!2024')
                print(f'👤 User ID: {existing_user.id}')
                return True
            
            # Create test user
            user = User(email='test@example.com', name='Test User')
            user.set_password('TestPassword!2024')
            db.session.add(user)
            db.session.commit()
            
            print('✅ Test user created successfully!')
            print(f'📧 Email: test@example.com')
            print(f'🔑 Password: TestPassword!2024')
            print(f'👤 User ID: {user.id}')
            
            return True
            
        except Exception as e:
            print(f'❌ Error creating user: {e}')
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 Creating test user for local development...")
    print("=" * 50)
    
    success = create_test_user()
    
    if success:
        print("\n🎉 You can now login at http://127.0.0.1:5000/login")
        print("Use the credentials above to access the application.")
    else:
        print("\n❌ Failed to create test user.")
#!/usr/bin/env python3
"""
Test Updated Model
Tests the updated Habit model in app.py with new fields
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

# Import from the main app.py file directly
import sys
sys.path.append('.')

# Execute the app.py file to get access to its variables
exec(open('app.py').read(), globals())

def test_updated_model():
    """Test the updated Habit model with new fields."""
    try:
        print("Testing updated Habit model...")
        
        with app.app_context():
            # Test 1: Create a habit with defaults
            print("\n📝 Test 1: Creating habit with defaults...")
            
            # First create a user
            user = User(email='test@example.com', name='Test User')
            db.session.add(user)
            db.session.commit()
            
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
            
            # Test 2: Create habit with explicit values
            print("\n📝 Test 2: Creating habit with explicit values...")
            habit2 = Habit(
                user_id=user.id,
                name='Read Books',
                execution_time=30,
                frequency=7,
                habit_type='useful',
                reward='Watch a movie'
            )
            db.session.add(habit2)
            db.session.commit()
            
            print(f"✅ Habit created with explicit values:")
            print(f"   - execution_time: {habit2.execution_time}")
            print(f"   - frequency: {habit2.frequency}")
            print(f"   - habit_type: {habit2.habit_type}")
            print(f"   - reward: {habit2.reward}")
            
            # Test 3: Test business rule validation
            print("\n📝 Test 3: Testing business rule validation...")
            
            # Test pleasant habit with reward (should fail)
            habit3 = Habit(
                user_id=user.id,
                name='Pleasant Habit',
                habit_type='pleasant',
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
            
            # Test 4: Test new methods
            print("\n📝 Test 4: Testing new methods...")
            
            print(f"Habit1 is pleasant: {habit1.is_pleasant_habit()}")
            print(f"Habit1 is useful: {habit1.is_useful_habit()}")
            print(f"Habit1 has reward: {habit1.has_reward()}")
            print(f"Habit1 execution time in minutes: {habit1.get_execution_time_minutes()}")
            print(f"Habit1 frequency description: {habit1.get_frequency_description()}")
            print(f"Habit1 can be completed today: {habit1.can_be_completed_today()}")
            
            # Test 5: Test relationships
            print("\n📝 Test 5: Testing relationships...")
            
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
            
            print("\n🎉 All updated model tests completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error testing updated model: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = test_updated_model()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
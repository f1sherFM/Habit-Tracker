"""
Performance and Load Testing Suite
Tests concurrent user access, connection pooling, and database performance under load
"""

import pytest
import time
import threading
import concurrent.futures
from datetime import datetime, timezone, date
from hypothesis import given, strategies as st, settings
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Import application modules
from app import app, db, User, Habit, HabitLog
from database_config import DatabaseConfig


class TestPerformanceAndLoad:
    """Test suite for performance and load testing"""
    
    @pytest.fixture(scope="function")
    def test_app(self):
        """Create a test Flask application with connection pooling"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        # Configure connection pooling for testing (SQLite compatible)
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'connect_args': {'check_same_thread': False}
        }
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture(scope="function")
    def client(self, test_app):
        """Create a test client"""
        return test_app.test_client()
    
    def test_concurrent_user_registration(self, test_app):
        """
        Test concurrent user registration to verify database handles multiple simultaneous users
        **Validates: Requirements 1.5**
        """
        def create_user(user_id):
            """Create a user in a separate thread"""
            with test_app.app_context():
                try:
                    user = User(email=f'user{user_id}@example.com')
                    user.set_password('SecureP@ssw0rd!')
                    db.session.add(user)
                    db.session.commit()
                    return True
                except Exception as e:
                    print(f"Error creating user {user_id}: {e}")
                    return False
        
        # Test with 20 concurrent user registrations
        num_users = 20
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_user, i) for i in range(num_users)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all users were created successfully
        successful_creations = sum(results)
        assert successful_creations == num_users, f"Expected {num_users} users, got {successful_creations}"
        
        # Verify users exist in database
        with test_app.app_context():
            total_users = User.query.count()
            assert total_users == num_users, f"Database should contain {num_users} users"
    
    def test_concurrent_habit_operations(self, test_app):
        """
        Test concurrent habit creation and modification
        **Validates: Requirements 1.5**
        """
        with test_app.app_context():
            # Create a test user first
            user = User(email='testuser@example.com')
            user.set_password('SecureP@ssw0rd!')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        
        def create_habit(habit_id):
            """Create a habit in a separate thread"""
            with test_app.app_context():
                try:
                    habit = Habit(
                        user_id=user_id,
                        name=f'Habit {habit_id}',
                        description=f'Description for habit {habit_id}'
                    )
                    db.session.add(habit)
                    db.session.commit()
                    return True
                except Exception as e:
                    print(f"Error creating habit {habit_id}: {e}")
                    return False
        
        # Test with 15 concurrent habit creations
        num_habits = 15
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(create_habit, i) for i in range(num_habits)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all habits were created successfully
        successful_creations = sum(results)
        assert successful_creations == num_habits, f"Expected {num_habits} habits, got {successful_creations}"
        
        # Verify habits exist in database
        with test_app.app_context():
            total_habits = Habit.query.filter_by(user_id=user_id).count()
            assert total_habits == num_habits, f"Database should contain {num_habits} habits for user"
    
    def test_concurrent_habit_logging(self, test_app):
        """
        Test concurrent habit log operations
        **Validates: Requirements 1.5**
        """
        with test_app.app_context():
            # Create test user and habit
            user = User(email='loguser@example.com')
            user.set_password('SecureP@ssw0rd!')
            db.session.add(user)
            db.session.commit()
            
            habit = Habit(user_id=user.id, name='Test Habit', description='Test')
            db.session.add(habit)
            db.session.commit()
            habit_id = habit.id
        
        def create_habit_log(day_offset):
            """Create a habit log for a specific day"""
            with test_app.app_context():
                try:
                    log_date = date.today().replace(day=1) if day_offset == 0 else date.today().replace(day=day_offset + 1)
                    habit_log = HabitLog(
                        habit_id=habit_id,
                        date=log_date,
                        completed=True
                    )
                    db.session.add(habit_log)
                    db.session.commit()
                    return True
                except Exception as e:
                    print(f"Error creating habit log for day {day_offset}: {e}")
                    return False
        
        # Test with 10 concurrent habit log creations for different days
        num_logs = 10
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_habit_log, i) for i in range(num_logs)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all logs were created successfully
        successful_creations = sum(results)
        assert successful_creations == num_logs, f"Expected {num_logs} logs, got {successful_creations}"
        
        # Verify logs exist in database
        with test_app.app_context():
            total_logs = HabitLog.query.filter_by(habit_id=habit_id).count()
            assert total_logs == num_logs, f"Database should contain {num_logs} habit logs"
    
    def test_database_connection_pooling(self, test_app):
        """
        Test that connection pooling works correctly under concurrent load
        **Validates: Requirements 5.4**
        """
        def perform_database_operations(thread_id):
            """Perform multiple database operations in a thread"""
            with test_app.app_context():
                operations_completed = 0
                try:
                    # Create user
                    user = User(email=f'pooltest{thread_id}@example.com')
                    user.set_password('SecureP@ssw0rd!')
                    db.session.add(user)
                    db.session.commit()
                    operations_completed += 1
                    
                    # Create habit
                    habit = Habit(user_id=user.id, name=f'Pool Test Habit {thread_id}')
                    db.session.add(habit)
                    db.session.commit()
                    operations_completed += 1
                    
                    # Create habit log
                    habit_log = HabitLog(habit_id=habit.id, date=date.today(), completed=True)
                    db.session.add(habit_log)
                    db.session.commit()
                    operations_completed += 1
                    
                    # Query operations
                    User.query.filter_by(email=f'pooltest{thread_id}@example.com').first()
                    operations_completed += 1
                    
                    Habit.query.filter_by(user_id=user.id).all()
                    operations_completed += 1
                    
                    HabitLog.query.filter_by(habit_id=habit.id).all()
                    operations_completed += 1
                    
                    return operations_completed
                except Exception as e:
                    print(f"Error in thread {thread_id}: {e}")
                    return operations_completed
        
        # Test with 12 concurrent threads performing database operations
        num_threads = 12
        expected_operations_per_thread = 6
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(perform_database_operations, i) for i in range(num_threads)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.time()
        
        # Verify all operations completed successfully
        total_operations = sum(results)
        expected_total = num_threads * expected_operations_per_thread
        assert total_operations == expected_total, f"Expected {expected_total} operations, got {total_operations}"
        
        # Verify reasonable performance (should complete within 10 seconds)
        execution_time = end_time - start_time
        assert execution_time < 10.0, f"Operations took too long: {execution_time:.2f} seconds"
        
        print(f"Connection pooling test completed in {execution_time:.2f} seconds")
    
    def test_database_performance_under_load(self, test_app):
        """
        Test database performance with high volume of operations
        **Validates: Requirements 1.5, 5.4**
        """
        with test_app.app_context():
            # Create base user for testing
            base_user = User(email='loadtest@example.com')
            base_user.set_password('SecureP@ssw0rd!')
            db.session.add(base_user)
            db.session.commit()
            base_user_id = base_user.id
        
        def bulk_operations(batch_id):
            """Perform bulk database operations"""
            with test_app.app_context():
                operations_count = 0
                try:
                    # Create multiple habits in batch
                    habits = []
                    for i in range(5):  # 5 habits per batch
                        habit = Habit(
                            user_id=base_user_id,
                            name=f'Load Test Habit {batch_id}-{i}',
                            description=f'Batch {batch_id} Habit {i}'
                        )
                        habits.append(habit)
                        db.session.add(habit)
                    
                    db.session.commit()
                    operations_count += len(habits)
                    
                    # Create habit logs for each habit
                    for habit in habits:
                        for day in range(3):  # 3 days of logs per habit
                            log_date = date.today().replace(day=day + 1) if day < 28 else date.today()
                            habit_log = HabitLog(
                                habit_id=habit.id,
                                date=log_date,
                                completed=day % 2 == 0  # Alternate completion status
                            )
                            db.session.add(habit_log)
                            operations_count += 1
                    
                    db.session.commit()
                    
                    # Perform some queries
                    User.query.filter_by(id=base_user_id).first()
                    Habit.query.filter_by(user_id=base_user_id).count()
                    operations_count += 2
                    
                    return operations_count
                except Exception as e:
                    print(f"Error in batch {batch_id}: {e}")
                    return operations_count
        
        # Test with 8 concurrent batches
        num_batches = 8
        expected_operations_per_batch = 5 + (5 * 3) + 2  # 5 habits + 15 logs + 2 queries = 22
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(bulk_operations, i) for i in range(num_batches)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.time()
        
        # Verify all operations completed
        total_operations = sum(results)
        expected_total = num_batches * expected_operations_per_batch
        assert total_operations == expected_total, f"Expected {expected_total} operations, got {total_operations}"
        
        # Verify data was actually created
        with test_app.app_context():
            total_habits = Habit.query.filter_by(user_id=base_user_id).count()
            total_logs = HabitLog.query.join(Habit).filter(Habit.user_id == base_user_id).count()
            
            expected_habits = num_batches * 5
            expected_logs = num_batches * 5 * 3
            
            assert total_habits == expected_habits, f"Expected {expected_habits} habits, got {total_habits}"
            assert total_logs == expected_logs, f"Expected {expected_logs} logs, got {total_logs}"
        
        # Performance assertion - should complete within reasonable time
        execution_time = end_time - start_time
        assert execution_time < 15.0, f"Bulk operations took too long: {execution_time:.2f} seconds"
        
        print(f"Load test completed: {total_operations} operations in {execution_time:.2f} seconds")
        print(f"Average operations per second: {total_operations / execution_time:.2f}")
    
    def test_connection_timeout_handling(self, test_app):
        """
        Test that the application handles connection timeouts gracefully
        **Validates: Requirements 5.4**
        """
        db_config = DatabaseConfig()
        
        # Test connection parameters include timeout settings
        connection_params = db_config.get_connection_params()
        
        # Verify timeout parameters are configured
        if 'connect_args' in connection_params:
            connect_args = connection_params['connect_args']
            # For SQLite, check timeout parameter
            if 'timeout' in connect_args:
                assert connect_args['timeout'] > 0, "Timeout should be positive"
        
        # Verify pool timeout is configured for production databases
        if 'pool_timeout' in connection_params:
            assert connection_params['pool_timeout'] > 0, "Pool timeout should be positive"
        
        # Test that connection validation works
        validation_result = db_config.validate_connection()
        assert isinstance(validation_result, bool), "Connection validation should return boolean"
    
    def test_memory_usage_under_load(self, test_app):
        """
        Test that memory usage remains reasonable under load
        **Validates: Requirements 1.5**
        """
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with test_app.app_context():
            # Create a user for testing
            user = User(email='memorytest@example.com')
            user.set_password('SecureP@ssw0rd!')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            
            # Create a large number of habits and logs
            for i in range(100):  # Create 100 habits
                habit = Habit(
                    user_id=user_id,
                    name=f'Memory Test Habit {i}',
                    description=f'Testing memory usage with habit {i}'
                )
                db.session.add(habit)
                
                if i % 10 == 0:  # Commit every 10 habits
                    db.session.commit()
            
            db.session.commit()
            
            # Create habit logs
            habits = Habit.query.filter_by(user_id=user_id).all()
            for habit in habits:
                for day in range(7):  # 7 days of logs per habit
                    try:
                        log_date = date.today().replace(day=day + 1) if day < 28 else date.today()
                        habit_log = HabitLog(
                            habit_id=habit.id,
                            date=log_date,
                            completed=day % 2 == 0
                        )
                        db.session.add(habit_log)
                    except ValueError:
                        # Skip invalid dates
                        continue
                
                if habit.id % 20 == 0:  # Commit every 20 habits worth of logs
                    db.session.commit()
            
            db.session.commit()
            
            # Perform some queries to load data into memory
            all_habits = Habit.query.filter_by(user_id=user_id).all()
            for habit in all_habits[:10]:  # Check first 10 habits
                logs = HabitLog.query.filter_by(habit_id=habit.id).all()
                assert len(logs) > 0, "Should have logs for habit"
        
        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory usage increased by {memory_increase:.2f}MB, which is too high"
        
        print(f"Memory usage: Initial {initial_memory:.2f}MB, Final {final_memory:.2f}MB, Increase {memory_increase:.2f}MB")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
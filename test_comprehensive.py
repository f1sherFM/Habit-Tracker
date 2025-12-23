"""
Comprehensive Test Suite for Database Persistence Fix
Tests user registration, login flow, habit creation and persistence
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, timezone, date, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.strategies import text, emails, integers, booleans, dates
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash

# Import application modules
from app import app, db, User, Habit, HabitLog
from database_config import DatabaseConfig
from migration_service import MigrationService
from password_security import PasswordValidator, SecurePasswordHasher


class TestDatabasePersistence:
    """Test suite for database persistence functionality"""
    
    @pytest.fixture(scope="function")
    def test_app(self):
        """Create a test Flask application with in-memory database"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        # Remove engine options that don't work with SQLite
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
    
    @pytest.fixture(scope="function")
    def temp_db_file(self):
        """Create a temporary SQLite database file"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass
    
    # Property 1: User Registration Persistence
    @given(
        email=emails(),
        password=text(min_size=8, max_size=50).filter(lambda x: any(c.isdigit() for c in x) and any(c.isupper() for c in x) and any(c.islower() for c in x))
    )
    @settings(max_examples=100, deadline=None)
    def test_user_registration_persistence(self, email, password):
        """
        **Feature: database-persistence-fix, Property 1: User Registration Persistence**
        For any user registration with valid credentials, storing the user in the database 
        and then querying for that user should return the same user data
        **Validates: Requirements 1.1**
        """
        # Create a fresh app context for each test
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'connect_args': {'check_same_thread': False}
        }
        
        with app.app_context():
            db.create_all()
            
            # Create user with valid data
            user = User(email=email)
            try:
                user.set_password(password)
            except ValueError:
                # Skip if password doesn't meet requirements
                return
            
            db.session.add(user)
            db.session.commit()
            
            # Query for the user
            retrieved_user = User.query.filter_by(email=email).first()
            
            # Verify persistence
            assert retrieved_user is not None
            assert retrieved_user.email == email
            assert retrieved_user.check_password(password)
            assert retrieved_user.id == user.id
            
            db.drop_all()
    
    # Property 2: User Login Data Retrieval
    @given(
        email=emails(),
        password=text(min_size=8, max_size=50).filter(lambda x: any(c.isdigit() for c in x) and any(c.isupper() for c in x) and any(c.islower() for c in x))
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_user_login_data_retrieval(self, test_app, email, password):
        """
        **Feature: database-persistence-fix, Property 2: User Login Data Retrieval**
        For any registered user, attempting to login with correct credentials should 
        successfully retrieve and authenticate the user from persistent storage
        **Validates: Requirements 1.2**
        """
        with test_app.app_context():
            # Create and store user
            user = User(email=email)
            try:
                user.set_password(password)
            except ValueError:
                # Skip if password doesn't meet requirements
                return
            
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            
            # Clear session to simulate fresh retrieval
            db.session.expunge_all()
            
            # Retrieve user for login
            login_user = User.query.filter_by(email=email).first()
            
            # Verify login data retrieval
            assert login_user is not None
            assert login_user.id == user_id
            assert login_user.email == email
            assert login_user.check_password(password)
    
    # Property 3: Habit Data Persistence
    @given(
        email=emails(),
        habit_name=text(min_size=1, max_size=100).filter(lambda x: x.strip() and x.isalnum()),
        habit_description=text(max_size=500)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_habit_data_persistence(self, test_app, email, habit_name, habit_description):
        """
        **Feature: database-persistence-fix, Property 3: Habit Data Persistence**
        For any habit created by a user, storing the habit and then querying for it 
        should return the same habit data with all properties intact
        **Validates: Requirements 1.3**
        """
        with test_app.app_context():
            # Create user first
            user = User(email=email)
            user.password_hash = "dummy_hash"  # Skip password validation for this test
            db.session.add(user)
            db.session.commit()
            
            # Create habit
            habit = Habit(
                user_id=user.id,
                name=habit_name,
                description=habit_description
            )
            db.session.add(habit)
            db.session.commit()
            habit_id = habit.id
            
            # Clear session to simulate fresh retrieval
            db.session.expunge_all()
            
            # Query for the habit
            retrieved_habit = Habit.query.filter_by(id=habit_id).first()
            
            # Verify persistence
            assert retrieved_habit is not None
            assert retrieved_habit.name == habit_name
            assert retrieved_habit.description == habit_description
            assert retrieved_habit.user_id == user.id
            assert retrieved_habit.id == habit_id
    
    # Property 4: Environment-Based Database Selection
    def test_environment_based_database_selection(self):
        """
        **Feature: database-persistence-fix, Property 4: Environment-Based Database Selection**
        For any environment configuration, the system should automatically select 
        the appropriate database URI based on environment variables
        **Validates: Requirements 2.5**
        """
        db_config = DatabaseConfig()
        
        # Test that we get a valid database URI
        uri = db_config.get_database_uri()
        assert uri is not None
        assert isinstance(uri, str)
        assert len(uri) > 0
        
        # Test that URI starts with a valid database scheme
        valid_schemes = ['sqlite://', 'postgresql://', 'postgres://']
        assert any(uri.startswith(scheme) for scheme in valid_schemes)
        
        # Test environment detection
        is_prod = db_config.is_production()
        assert isinstance(is_prod, bool)
    
    # Property 5: Database Connection Error Handling
    def test_database_connection_error_handling(self):
        """
        **Feature: database-persistence-fix, Property 5: Database Connection Error Handling**
        For any invalid database credentials or connection parameters, the system should 
        provide clear, user-friendly error messages without exposing sensitive information
        **Validates: Requirements 2.4**
        """
        db_config = DatabaseConfig()
        
        # Test various error scenarios
        test_errors = [
            Exception("connection timeout"),
            Exception("authentication failed"),
            Exception("host not found"),
            Exception("ssl certificate error"),
            Exception("database does not exist"),
            Exception("unknown error")
        ]
        
        for error in test_errors:
            error_message = db_config.get_error_message(error)
            
            # Verify error message is user-friendly
            assert isinstance(error_message, str)
            assert len(error_message) > 0
            assert "password" not in error_message.lower() or "check your database credentials" in error_message.lower()
            assert "exception" not in error_message.lower()
            assert "traceback" not in error_message.lower()


class TestMigrationService:
    """Test suite for migration service functionality"""
    
    @pytest.fixture(scope="function")
    def temp_source_db(self):
        """Create a temporary source SQLite database with test data"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Create test database with sample data
        import sqlite3
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                google_id TEXT,
                github_id TEXT,
                name TEXT,
                avatar_url TEXT,
                created_at TEXT,
                updated_at TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE habits (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT,
                updated_at TEXT,
                is_archived BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE habit_logs (
                id INTEGER PRIMARY KEY,
                habit_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                created_at TEXT,
                FOREIGN KEY (habit_id) REFERENCES habits (id),
                UNIQUE(habit_id, date)
            )
        ''')
        
        # Insert test data
        cursor.execute('''
            INSERT INTO users (id, email, password_hash, name, created_at, updated_at, is_active)
            VALUES (1, 'test@example.com', 'hash123', 'Test User', '2023-01-01T00:00:00Z', '2023-01-01T00:00:00Z', 1)
        ''')
        
        cursor.execute('''
            INSERT INTO habits (id, user_id, name, description, created_at, updated_at, is_archived)
            VALUES (1, 1, 'Exercise', 'Daily exercise routine', '2023-01-01T00:00:00Z', '2023-01-01T00:00:00Z', 0)
        ''')
        
        cursor.execute('''
            INSERT INTO habit_logs (id, habit_id, date, completed, created_at)
            VALUES (1, 1, '2023-01-01', 1, '2023-01-01T00:00:00Z')
        ''')
        
        conn.commit()
        conn.close()
        
        yield path
        
        try:
            os.unlink(path)
        except OSError:
            pass
    
    @pytest.fixture(scope="function")
    def temp_target_db(self):
        """Create a temporary target database URI"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        target_uri = f"sqlite:///{path}"
        
        # Create target database with proper schema
        from sqlalchemy import create_engine
        engine = create_engine(target_uri)
        
        with app.app_context():
            # Use app's metadata to create tables
            db.metadata.create_all(engine)
        
        yield target_uri
        
        try:
            os.unlink(path)
        except OSError:
            pass
    
    # Property 6: Migration Data Preservation
    def test_migration_data_preservation(self, temp_source_db, temp_target_db):
        """
        **Feature: database-persistence-fix, Property 6: Migration Data Preservation**
        For any existing user data, running the migration process should preserve 
        all user accounts, habits, and habit logs without data loss
        **Validates: Requirements 3.1, 3.2**
        """
        migration_service = MigrationService()
        
        # Run migration
        success = migration_service.run_full_migration(temp_source_db, temp_target_db, verify=False)
        assert success, "Migration should complete successfully"
        
        # Verify data preservation by checking target database
        from sqlalchemy import create_engine, text
        target_engine = create_engine(temp_target_db)
        
        with target_engine.connect() as conn:
            # Check users
            users = conn.execute(text("SELECT * FROM users")).fetchall()
            assert len(users) == 1
            assert users[0][1] == 'test@example.com'  # email
            assert users[0][3] == 'Test User'  # name
            
            # Check habits
            habits = conn.execute(text("SELECT * FROM habits")).fetchall()
            assert len(habits) == 1
            assert habits[0][2] == 'Exercise'  # name
            assert habits[0][3] == 'Daily exercise routine'  # description
            
            # Check habit logs
            logs = conn.execute(text("SELECT * FROM habit_logs")).fetchall()
            assert len(logs) == 1
            assert logs[0][3] == 1  # completed
    
    # Property 7: Migration Data Integrity Verification
    def test_migration_integrity_verification(self, temp_source_db, temp_target_db):
        """
        **Feature: database-persistence-fix, Property 7: Migration Data Integrity Verification**
        For any completed migration, the data counts and essential relationships 
        in the target database should match the source database
        **Validates: Requirements 3.3**
        """
        migration_service = MigrationService()
        
        # Run migration with verification
        success = migration_service.run_full_migration(temp_source_db, temp_target_db, verify=True)
        assert success, "Migration with verification should complete successfully"
        
        # Run standalone verification
        verification_success = migration_service.verify_migration(temp_source_db, temp_target_db)
        assert verification_success, "Data integrity verification should pass"
        
        # Check migration log for verification steps
        log = migration_service.get_migration_log()
        verification_entries = [entry for entry in log if 'Verification' in entry['step']]
        assert len(verification_entries) > 0, "Should have verification log entries"
        
        # Ensure all verification steps passed
        failed_verifications = [entry for entry in verification_entries if entry['status'] == 'FAILED']
        assert len(failed_verifications) == 0, "No verification steps should fail"


class TestPasswordSecurity:
    """Test suite for password security functionality"""
    
    # Property 8: Password Security
    @given(password=text(min_size=8, max_size=128))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_password_security(self, password):
        """
        **Feature: database-persistence-fix, Property 8: Password Security**
        For any user password, the stored password hash should never match 
        the plain text password and should use secure hashing algorithms
        **Validates: Requirements 5.1**
        """
        try:
            # Hash the password
            password_hash = SecurePasswordHasher.hash_password(password)
            
            # Verify hash properties
            assert password_hash != password, "Hash should never equal plain text password"
            assert len(password_hash) > len(password), "Hash should be longer than original password"
            assert 'pbkdf2' in password_hash or password_hash.startswith('$'), "Hash should use secure format"
            
            # Verify password verification works
            assert SecurePasswordHasher.verify_password(password, password_hash), "Should verify correct password"
            
            # Verify wrong password fails
            wrong_password = password + "wrong"
            assert not SecurePasswordHasher.verify_password(wrong_password, password_hash), "Should reject wrong password"
            
        except ValueError:
            # Password doesn't meet security requirements, which is acceptable
            pass


class TestSQLInjectionPrevention:
    """Test suite for SQL injection prevention"""
    
    @pytest.fixture(scope="function")
    def test_app(self):
        """Create a test Flask application"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        # Remove engine options that don't work with SQLite
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
    
    # Property 9: SQL Injection Prevention
    @given(
        malicious_input=st.one_of(
            st.just("'; DROP TABLE users; --"),
            st.just("' OR '1'='1"),
            st.just("admin'--"),
            st.just("' UNION SELECT * FROM users --"),
            st.just("'; INSERT INTO users VALUES ('hacker', 'pass'); --")
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_sql_injection_prevention(self, test_app, client, malicious_input):
        """
        **Feature: database-persistence-fix, Property 9: SQL Injection Prevention**
        For any database query executed through the ORM, the query should use 
        parameterized statements and not allow direct SQL injection
        **Validates: Requirements 5.3**
        """
        with test_app.app_context():
            # Create a test user first
            user = User(email='test@example.com')
            user.password_hash = 'dummy_hash'
            db.session.add(user)
            db.session.commit()
            
            # Test SQL injection in login form
            response = client.post('/login', data={
                'email': malicious_input,
                'password': 'password'
            })
            
            # Should not crash or expose database errors
            assert response.status_code in [200, 302], "Should handle malicious input gracefully"
            
            # Verify database integrity - user table should still exist and be intact
            users = User.query.all()
            assert len(users) == 1, "Database should not be compromised"
            assert users[0].email == 'test@example.com', "Original data should be intact"
            
            # Test SQL injection in habit creation
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
            
            response = client.post('/add-habit', data={
                'name': malicious_input,
                'description': 'test description'
            })
            
            # Should handle malicious input without crashing
            assert response.status_code in [200, 302], "Should handle malicious habit input gracefully"
            
            # Verify no malicious habits were created
            habits = Habit.query.all()
            for habit in habits:
                assert malicious_input not in habit.name, "Malicious input should be sanitized or rejected"


class TestApplicationFlow:
    """Integration tests for complete application flows"""
    
    @pytest.fixture(scope="function")
    def test_app(self):
        """Create a test Flask application"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        # Remove engine options that don't work with SQLite
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
    
    def test_complete_user_registration_and_habit_flow(self, test_app, client):
        """
        Test complete user registration, login, and habit creation flow
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        """
        with test_app.app_context():
            # Step 1: Register user
            response = client.post('/register', data={
                'email': 'testuser@example.com',
                'password': 'SecurePass123!',
                'confirm_password': 'SecurePass123!'
            })
            assert response.status_code == 302, "Registration should redirect"
            
            # Verify user was created
            user = User.query.filter_by(email='testuser@example.com').first()
            assert user is not None, "User should be created in database"
            
            # Step 2: Login
            response = client.post('/login', data={
                'email': 'testuser@example.com',
                'password': 'SecurePass123!'
            })
            assert response.status_code == 302, "Login should redirect"
            
            # Step 3: Create habit
            response = client.post('/add-habit', data={
                'name': 'Daily Exercise',
                'description': 'Exercise for 30 minutes daily'
            })
            assert response.status_code == 302, "Habit creation should redirect"
            
            # Verify habit was created
            habit = Habit.query.filter_by(name='Daily Exercise').first()
            assert habit is not None, "Habit should be created in database"
            assert habit.user_id == user.id, "Habit should belong to the user"
            
            # Step 4: Toggle habit completion
            today = date.today().strftime('%Y-%m-%d')
            response = client.post(f'/toggle-habit/{habit.id}/{today}')
            assert response.status_code == 200, "Habit toggle should succeed"
            
            # Verify habit log was created
            habit_log = HabitLog.query.filter_by(habit_id=habit.id, date=date.today()).first()
            assert habit_log is not None, "Habit log should be created"
            assert habit_log.completed == True, "Habit should be marked as completed"
    
    def test_data_persistence_across_sessions(self, test_app, client):
        """
        Test that data persists across different sessions
        **Validates: Requirements 1.4**
        """
        with test_app.app_context():
            # Create user and habit in first session
            user = User(email='persistent@example.com')
            user.set_password('SecurePass123!')
            db.session.add(user)
            db.session.commit()
            
            habit = Habit(user_id=user.id, name='Persistent Habit', description='Test persistence')
            db.session.add(habit)
            db.session.commit()
            
            habit_log = HabitLog(habit_id=habit.id, date=date.today(), completed=True)
            db.session.add(habit_log)
            db.session.commit()
            
            # Clear session to simulate application restart
            db.session.expunge_all()
            
            # Verify data persists in new session
            persistent_user = User.query.filter_by(email='persistent@example.com').first()
            assert persistent_user is not None, "User should persist across sessions"
            
            persistent_habit = Habit.query.filter_by(name='Persistent Habit').first()
            assert persistent_habit is not None, "Habit should persist across sessions"
            assert persistent_habit.user_id == persistent_user.id, "Relationships should persist"
            
            persistent_log = HabitLog.query.filter_by(habit_id=persistent_habit.id).first()
            assert persistent_log is not None, "Habit log should persist across sessions"
            assert persistent_log.completed == True, "Habit completion status should persist"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
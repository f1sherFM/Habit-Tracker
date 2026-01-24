"""
API Integration Tests for Habit Tracker

Tests complete API workflows including validation, authorization, and CORS
"""
import pytest
import json
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.models import init_db, get_models
from app.models.habit_types import HabitType
from app.services.user_service import UserService
from app.exceptions import ValidationError, AuthorizationError


class TestAPIIntegration:
    """Integration tests for API endpoints with full workflows"""
    
    @pytest.fixture
    def app(self):
        """Create test application with API configuration"""
        # Set required environment variables for testing
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-for-integration-tests-that-is-long-enough',
            'FLASK_ENV': 'testing',
            'DATABASE_URL': 'sqlite:///:memory:'
        }):
            app = create_app('testing')
            with app.app_context():
                db.create_all()
                yield app
                db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def models(self, app):
        """Get model classes"""
        return get_models()
    
    @pytest.fixture
    def test_user(self, app, models):
        """Create a test user with authentication"""
        User, Habit, HabitLog = models
        user_service = UserService()
        
        user = user_service.create_user(
            email='test@example.com',
            password='TestPassword9!@#$%',
            name='Test User'
        )
        db.session.commit()
        return user
    
    @pytest.fixture
    def another_user(self, app, models):
        """Create another test user for authorization tests"""
        User, Habit, HabitLog = models
        user_service = UserService()
        
        user = user_service.create_user(
            email='another@example.com',
            password='AnotherPassword8!@#$%',
            name='Another User'
        )
        db.session.commit()
        return user
    
    def test_complete_habit_crud_workflow(self, authenticated_client, test_user):
        """Test complete CRUD workflow for habits through API"""
        
        # Use authenticated client instead of mocking
        client = authenticated_client
        
        # 1. CREATE - Post new habit
        habit_data = {
        'name': 'Morning Exercise',
        'description': 'Daily morning workout routine',
        'execution_time': 60,
        'frequency': 7,
        'habit_type': 'useful',
        'reward': 'Healthy breakfast'
        }
        
        response = client.post(
        '/api/habits',
        data=json.dumps(habit_data),
        content_type='application/json'
        )
        
        assert response.status_code == 201
        created_habit = response.get_json()['habit']
        assert created_habit['name'] == 'Morning Exercise'
        assert created_habit['habit_type'] == 'useful'
        assert created_habit['reward'] == 'Healthy breakfast'
        habit_id = created_habit['id']
        
        # 2. READ - Get all habits
        response = client.get('/api/habits')
        assert response.status_code == 200
        
        habits_data = response.get_json()
        assert habits_data['total'] == 1
        assert len(habits_data['habits']) == 1
        assert habits_data['habits'][0]['name'] == 'Morning Exercise'
        
        # 3. READ - Get specific habit
        response = client.get(f'/api/habits/{habit_id}')
        assert response.status_code == 200
        
        habit_data = response.get_json()['habit']
        assert habit_data['name'] == 'Morning Exercise'
        assert habit_data['id'] == habit_id
        
        # 4. UPDATE - Modify habit
        update_data = {
            'name': 'Updated Morning Exercise',
            'execution_time': 90,
            'description': 'Updated workout routine'
        }
        
        response = client.put(
            f'/api/habits/{habit_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        updated_habit = response.get_json()['habit']
        assert updated_habit['name'] == 'Updated Morning Exercise'
        assert updated_habit['execution_time'] == 90
        assert updated_habit['description'] == 'Updated workout routine'
        assert updated_habit['reward'] == 'Healthy breakfast'  # Unchanged
        
        # 5. ARCHIVE - Soft delete habit
        response = client.post(f'/api/habits/{habit_id}/archive')
        assert response.status_code == 200
        
        archived_habit = response.get_json()['habit']
        assert archived_habit['is_archived'] is True
        
        # 6. Verify archived habit not in default list
        response = client.get('/api/habits')
        assert response.status_code == 200
        
        habits_data = response.get_json()
        assert habits_data['total'] == 0
        assert len(habits_data['habits']) == 0
        
        # 7. Get habits including archived
        response = client.get('/api/habits?include_archived=true')
        assert response.status_code == 200
        
        habits_data = response.get_json()
        assert habits_data['total'] == 1
        assert habits_data['habits'][0]['is_archived'] is True
        
        # 8. RESTORE - Unarchive habit
        response = client.post(f'/api/habits/{habit_id}/restore')
        assert response.status_code == 200
        
        restored_habit = response.get_json()['habit']
        assert restored_habit['is_archived'] is False
        
        # 9. DELETE - Hard delete habit
        response = client.delete(f'/api/habits/{habit_id}')
        assert response.status_code == 204
        
        # 10. Verify habit is deleted
        response = client.get(f'/api/habits/{habit_id}')
        assert response.status_code == 404
    
    def test_validation_workflow_through_api(self, authenticated_client, test_user):
        """Test that validation works properly through API endpoints"""
        
        client = authenticated_client
        
        # Test execution time validation (> 120 seconds)
        invalid_habit_data = {
            'name': 'Long Exercise',
            'execution_time': 150,  # Invalid
            'frequency': 7,
            'habit_type': 'useful'
        }
        
        response = client.post(
            '/api/habits',
            data=json.dumps(invalid_habit_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        error_data = response.get_json()
        assert error_data['error']['code'] == 'VALIDATION_ERROR'
        assert any('120 секунд' in detail['message'] for detail in error_data['error']['details'])
        
        # Test frequency validation (< 7 days)
        invalid_habit_data = {
            'name': 'Daily Exercise',
            'execution_time': 60,
            'frequency': 3,  # Invalid
            'habit_type': 'useful'
        }
        
        response = client.post(
            '/api/habits',
            data=json.dumps(invalid_habit_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        error_data = response.get_json()
        assert error_data['error']['code'] == 'VALIDATION_ERROR'
        assert any('7 дней' in detail['message'] for detail in error_data['error']['details'])
        
        # Test pleasant habit with reward (should fail)
        invalid_habit_data = {
            'name': 'Watch TV',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': 'pleasant',
            'reward': 'Snacks'  # Invalid for pleasant habits
        }
        
        response = client.post(
            '/api/habits',
            data=json.dumps(invalid_habit_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        error_data = response.get_json()
        assert error_data['error']['code'] == 'VALIDATION_ERROR'
        assert any('приятная привычка не может иметь вознаграждение' in detail['message'].lower() 
                  for detail in error_data['error']['details'])
        
        # Test empty name validation
        invalid_habit_data = {
            'name': '',  # Invalid
            'execution_time': 60,
            'frequency': 7,
            'habit_type': 'useful'
        }
        
        response = client.post(
            '/api/habits',
            data=json.dumps(invalid_habit_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        error_data = response.get_json()
        # Could be validation error or missing required fields
        assert error_data['error']['code'] in ['VALIDATION_ERROR', 'MISSING_REQUIRED_FIELDS']
    
    def test_authorization_workflow_through_api(self, authenticated_client, test_user, another_user):
        """Test authorization checks through API endpoints"""
        
        client = authenticated_client
        
        # Create habit as first user
        habit_data = {
        'name': 'User 1 Habit',
        'execution_time': 60,
        'frequency': 7,
        'habit_type': 'useful'
        }
        
        response = client.post(
        '/api/habits',
        data=json.dumps(habit_data),
        content_type='application/json'
        )
        
        assert response.status_code == 201
        habit_id = response.get_json()['habit']['id']
        
        # Switch to second user
        with client.session_transaction() as sess:
        sess['_user_id'] = str(another_user.id)
        sess['_fresh'] = True
        
        # Try to get first user's habit (should fail)
        response = client.get(f'/api/habits/{habit_id}')
        assert response.status_code == 403
        error_data = response.get_json()
        assert error_data['error']['code'] == 'AUTHORIZATION_ERROR'
        
        # Try to update first user's habit (should fail)
        update_data = {'name': 'Hacked Habit'}
        response = client.put(
        f'/api/habits/{habit_id}',
        data=json.dumps(update_data),
        content_type='application/json'
        )
        
        assert response.status_code == 403
        error_data = response.get_json()
        assert error_data['error']['code'] == 'AUTHORIZATION_ERROR'
        
        # Try to delete first user's habit (should fail)
        response = client.delete(f'/api/habits/{habit_id}')
        assert response.status_code == 403
        error_data = response.get_json()
        assert error_data['error']['code'] == 'AUTHORIZATION_ERROR'
        
        # Try to archive first user's habit (should fail)
        response = client.post(f'/api/habits/{habit_id}/archive')
        assert response.status_code == 403
        error_data = response.get_json()
        assert error_data['error']['code'] == 'AUTHORIZATION_ERROR'
        
        # Verify second user can't see first user's habits in list
        response = client.get('/api/habits')
        assert response.status_code == 200
        habits_data = response.get_json()
        assert habits_data['total'] == 0
        assert len(habits_data['habits']) == 0
    
    def test_cors_headers_in_api_responses(self, authenticated_client, test_user):
        """Test that CORS headers are properly set in API responses"""
        
        # Create authenticated client
        with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
        
        # Test CORS headers in GET request
        response = client.get('/api/habits')
        assert response.status_code == 200
        
        # Check for security headers (these should be set by CORS config)
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
        assert 'X-XSS-Protection' in response.headers
        assert response.headers['X-XSS-Protection'] == '1; mode=block'
        
        # Test CORS headers in POST request
        habit_data = {
        'name': 'Test Habit',
        'execution_time': 60,
        'frequency': 7,
        'habit_type': 'useful'
        }
        
        response = client.post(
        '/api/habits',
        data=json.dumps(habit_data),
        content_type='application/json'
        )
        
        assert response.status_code == 201
        
        # Check security headers are present
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers
        assert 'X-XSS-Protection' in response.headers
    
    def test_api_error_handling_workflow(self, authenticated_client, test_user):
        """Test comprehensive error handling through API"""
        
        # Test 404 for non-existent habit
        response = authenticated_client.get('/api/habits/99999')
        assert response.status_code == 404
        error_data = response.get_json()
        assert error_data['error']['code'] == 'HABIT_NOT_FOUND'
        
        # Test 400 for invalid JSON
        response = authenticated_client.post(
        '/api/habits',
        data='invalid json',
        content_type='application/json'
        )
        assert response.status_code == 400
        
        # Test 400 for missing content type
        response = authenticated_client.post(
        '/api/habits',
        data=json.dumps({'name': 'Test'}),
        content_type='text/plain'
        )
        assert response.status_code == 400
        error_data = response.get_json()
        assert error_data['error']['code'] == 'INVALID_CONTENT_TYPE'
        
        # Test 400 for empty request body
        response = authenticated_client.put(
        '/api/habits/1',
        data='',
        content_type='application/json'
        )
        assert response.status_code == 400
        
        # Test 405 for unsupported method
        response = authenticated_client.patch('/api/habits')
        assert response.status_code == 405
        error_data = response.get_json()
        assert error_data['error']['code'] == 'METHOD_NOT_ALLOWED'
    
    def test_api_pagination_workflow(self, authenticated_client, test_user):
        """Test API pagination functionality"""
        
        # Create multiple habits
        for i in range(25):
        habit_data = {
            'name': f'Habit {i+1}',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': 'useful'
        }
        
        response = authenticated_client.post(
            '/api/habits',
            data=json.dumps(habit_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        # Test default pagination (page 1, 20 per page)
        response = authenticated_client.get('/api/habits')
        assert response.status_code == 200
        
        habits_data = response.get_json()
        assert habits_data['total'] == 25
        assert len(habits_data['habits']) == 20  # Default per_page
        assert habits_data['page'] == 1
        assert habits_data['per_page'] == 20
        assert habits_data['has_next'] is True
        assert habits_data['has_prev'] is False
        
        # Test page 2
        response = authenticated_client.get('/api/habits?page=2')
        assert response.status_code == 200
        
        habits_data = response.get_json()
        assert habits_data['total'] == 25
        assert len(habits_data['habits']) == 5  # Remaining habits
        assert habits_data['page'] == 2
        assert habits_data['has_next'] is False
        assert habits_data['has_prev'] is True
        
        # Test custom per_page
        response = authenticated_client.get('/api/habits?per_page=10')
        assert response.status_code == 200
        
        habits_data = response.get_json()
        assert len(habits_data['habits']) == 10
        assert habits_data['per_page'] == 10
        assert habits_data['has_next'] is True
        
        # Test max per_page limit (should cap at 100)
        response = authenticated_client.get('/api/habits?per_page=200')
        assert response.status_code == 200
        
        habits_data = response.get_json()
        assert habits_data['per_page'] == 100  # Capped at max
    
    def test_habit_type_filtering_workflow(self, authenticated_client, test_user):
        """Test filtering habits by type through API"""
        
        # Create useful habits
        for i in range(3):
        habit_data = {
            'name': f'Useful Habit {i+1}',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': 'useful',
            'reward': f'Reward {i+1}'
        }
        
        response = authenticated_client.post(
            '/api/habits',
            data=json.dumps(habit_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        # Create pleasant habits
        for i in range(2):
        habit_data = {
            'name': f'Pleasant Habit {i+1}',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': 'pleasant'
        }
        
        response = authenticated_client.post(
            '/api/habits',
            data=json.dumps(habit_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        # Test getting all habits
        response = authenticated_client.get('/api/habits')
        assert response.status_code == 200
        habits_data = response.get_json()
        assert habits_data['total'] == 5
        
        # Test filtering by useful type
        response = authenticated_client.get('/api/habits?type=useful')
        assert response.status_code == 200
        habits_data = response.get_json()
        assert habits_data['total'] == 3
        for habit in habits_data['habits']:
        assert habit['habit_type'] == 'useful'
        assert habit['reward'] is not None
        
        # Test filtering by pleasant type
        response = authenticated_client.get('/api/habits?type=pleasant')
        assert response.status_code == 200
        habits_data = response.get_json()
        assert habits_data['total'] == 2
        for habit in habits_data['habits']:
        assert habit['habit_type'] == 'pleasant'
        assert habit['reward'] is None
    
    def test_user_api_workflow(self, authenticated_client, test_user):
        """Test user API endpoints workflow"""
        
        # Create authenticated client
        with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
        
        # Test get current user
        response = client.get('/api/users/me')
        assert response.status_code == 200
        
        user_data = response.get_json()['user']
        assert user_data['id'] == test_user.id
        assert user_data['email'] == test_user.email
        assert user_data['name'] == test_user.name
        assert 'statistics' in user_data
        
        # Test update user profile
        update_data = {
        'name': 'Updated Test User',
        'avatar_url': 'https://example.com/avatar.jpg'
        }
        
        response = client.put(
        '/api/users/me',
        data=json.dumps(update_data),
        content_type='application/json'
        )
        
        assert response.status_code == 200
        updated_user = response.get_json()['user']
        assert updated_user['name'] == 'Updated Test User'
        assert updated_user['avatar_url'] == 'https://example.com/avatar.jpg'
        
        # Test get user statistics
        response = client.get('/api/users/me/statistics')
        assert response.status_code == 200
        
        stats_data = response.get_json()
        assert 'statistics' in stats_data
        
        # Test change password
        password_data = {
        'current_password': 'TestPassword9!@#$%',
        'new_password': 'NewPassword7!@#$%'
        }
        
        response = client.put(
        '/api/users/me/password',
        data=json.dumps(password_data),
        content_type='application/json'
        )
        
        assert response.status_code == 200
        assert 'Password changed successfully' in response.get_json()['message']
        
        # Test deactivate account
        response = client.post('/api/users/me/deactivate')
        assert response.status_code == 200
        
        deactivated_user = response.get_json()['user']
        assert deactivated_user['is_active'] is False
    
    def test_content_type_validation_workflow(self, authenticated_client):
        """Test content type validation across API endpoints"""
        
        # Test POST with wrong content type
        response = authenticated_client.post(
        '/api/habits',
        data='name=Test',
        content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code == 400
        error_data = response.get_json()
        assert error_data['error']['code'] == 'INVALID_CONTENT_TYPE'
        
        # Test PUT with wrong content type
        response = authenticated_client.put(
        '/api/habits/1',
        data='name=Test',
        content_type='text/plain'
        )
        assert response.status_code == 400
        error_data = response.get_json()
        assert error_data['error']['code'] == 'INVALID_CONTENT_TYPE'
        
        # Test user API with wrong content type
        response = authenticated_client.put(
        '/api/users/me',
        data='name=Test',
        content_type='text/html'
        )
        assert response.status_code == 400
        error_data = response.get_json()
        assert error_data['error']['code'] == 'INVALID_CONTENT_TYPE'
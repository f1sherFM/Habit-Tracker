"""
Habits API Endpoints

RESTful API for habit management using HabitService for business logic
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
from ..services.habit_service import (
    HabitService, ValidationError, AuthorizationError, 
    HabitNotFoundError, HabitServiceError
)
from ..services.user_service import UserService
import logging

# Create blueprint
habits_bp = Blueprint('habits_api', __name__, url_prefix='/api/habits')

# Services will be initialized when needed
habit_service = None
user_service = None

def get_habit_service():
    """Get or create HabitService instance"""
    global habit_service
    if habit_service is None:
        habit_service = HabitService()
    return habit_service

def get_user_service():
    """Get or create UserService instance"""
    global user_service
    if user_service is None:
        user_service = UserService()
    return user_service

logger = logging.getLogger(__name__)


@habits_bp.route('', methods=['GET'])
@login_required
def get_habits():
    """
    Get all habits for the current user with optional filtering
    
    Query parameters:
        include_archived: Include archived habits (default: false)
        type: Filter by habit type ('useful' or 'pleasant')
        category_id: Filter by category ID
        tag_ids: Filter by tag IDs (comma-separated)
        tracking_days: Number of days for tracking (1-30, default: 7)
        page: Page number (default: 1)
        per_page: Items per page (default: 20, max: 100)
    
    Returns:
        JSON response with habits list and metadata
    """
    try:
        # Get query parameters
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        habit_type = request.args.get('type')
        category_id = request.args.get('category_id', type=int)
        tag_ids_str = request.args.get('tag_ids', '')
        tracking_days = int(request.args.get('tracking_days', 7))
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # Max 100 per page
        
        # Validate tracking_days
        if tracking_days < 1 or tracking_days > 30:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'tracking_days must be between 1 and 30'
                }
            }), 400
        
        # Parse tag_ids
        tag_ids = []
        if tag_ids_str:
            try:
                tag_ids = [int(tag_id) for tag_id in tag_ids_str.split(',')]
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'tag_ids must be comma-separated integers'
                    }
                }), 400
        
        # Get habits using service layer
        habit_service = get_habit_service()
        habits = habit_service.get_user_habits(current_user.id, include_archived)
        
        # Apply type filter
        if habit_type:
            habits = [h for h in habits if h.habit_type and h.habit_type.value == habit_type]
        
        # Apply category filter
        if category_id:
            habits = [h for h in habits if h.category_id == category_id]
        
        # Apply tag filters (AND logic - habit must have all specified tags)
        if tag_ids:
            habits = [h for h in habits if all(any(tag.id == tag_id for tag in h.tags) for tag_id in tag_ids)]
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_habits = habits[start_idx:end_idx]
        
        # Convert to JSON format
        habits_data = []
        for habit in paginated_habits:
            habit_dict = {
                'id': habit.id,
                'name': habit.name,
                'description': habit.description,
                'execution_time': habit.execution_time,
                'frequency': habit.frequency,
                'habit_type': habit.habit_type.value if habit.habit_type else None,
                'reward': habit.reward,
                'related_habit_id': habit.related_habit_id,
                'category_id': habit.category_id,
                'tracking_days': habit.tracking_days or 7,
                'created_at': habit.created_at.isoformat() if habit.created_at else None,
                'updated_at': habit.updated_at.isoformat() if habit.updated_at else None,
                'is_archived': habit.is_archived
            }
            
            # Add computed fields
            if hasattr(habit, 'get_completion_rate'):
                habit_dict['completion_rate'] = habit.get_completion_rate()
            if hasattr(habit, 'can_be_completed_today'):
                habit_dict['can_complete_today'] = habit.can_be_completed_today()
            
            # Add tags
            if hasattr(habit, 'tags'):
                habit_dict['tags'] = [{'id': tag.id, 'name': tag.name} for tag in habit.tags]
            
            habits_data.append(habit_dict)
        
        return jsonify({
            'habits': habits_data,
            'total': len(habits),
            'page': page,
            'per_page': per_page,
            'has_next': end_idx < len(habits),
            'has_prev': page > 1,
            'tracking_days': tracking_days
        }), 200
        
    except HabitServiceError as e:
        logger.error(f"Service error getting habits for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Failed to retrieve habits',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting habits for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@habits_bp.route('', methods=['POST'])
@login_required
def create_habit():
    """
    Create a new habit
    
    Expected JSON payload:
    {
        "name": "Habit name",
        "description": "Optional description",
        "execution_time": 60,
        "frequency": 1,
        "habit_type": "useful",
        "reward": "Optional reward",
        "related_habit_id": null
    }
    
    Returns:
        JSON response with created habit data
    """
    try:
        # Validate content type
        if not request.is_json:
            return jsonify({
                'error': {
                    'code': 'INVALID_CONTENT_TYPE',
                    'message': 'Content-Type must be application/json'
                }
            }), 400
        
        habit_data = request.get_json()
        
        # Validate required fields
        if not habit_data or not habit_data.get('name'):
            return jsonify({
                'error': {
                    'code': 'MISSING_REQUIRED_FIELDS',
                    'message': 'Name is required'
                }
            }), 400
        
        # Convert habit_type string to enum if provided
        if 'habit_type' in habit_data:
            from ..models.habit_types import HabitType
            habit_type_str = habit_data['habit_type']
            if habit_type_str == 'useful':
                habit_data['habit_type'] = HabitType.USEFUL
            elif habit_type_str == 'pleasant':
                habit_data['habit_type'] = HabitType.PLEASANT
            # If it's already an enum, leave it as is
        
        # Create habit using service layer
        habit_service = get_habit_service()
        habit = habit_service.create_habit(current_user.id, habit_data)
        
        # Return created habit
        return jsonify({
            'habit': {
                'id': habit.id,
                'name': habit.name,
                'description': habit.description,
                'execution_time': habit.execution_time,
                'frequency': habit.frequency,
                'habit_type': habit.habit_type.value if habit.habit_type else None,
                'reward': habit.reward,
                'related_habit_id': habit.related_habit_id,
                'created_at': habit.created_at.isoformat() if habit.created_at else None,
                'updated_at': habit.updated_at.isoformat() if habit.updated_at else None,
                'is_archived': habit.is_archived
            }
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Habit data validation failed',
                'details': [{'message': error} for error in e.errors]
            }
        }), 400
    except HabitServiceError as e:
        logger.error(f"Service error creating habit for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Failed to create habit',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error creating habit for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@habits_bp.route('/<int:habit_id>', methods=['GET'])
@login_required
def get_habit(habit_id):
    """
    Get a specific habit by ID
    
    Args:
        habit_id: ID of the habit to retrieve
        
    Returns:
        JSON response with habit data
    """
    try:
        # Get habit using service layer (includes authorization check)
        habit_service = get_habit_service()
        habit = habit_service.get_habit_by_id(habit_id, current_user.id)
        
        return jsonify({
            'habit': {
                'id': habit.id,
                'name': habit.name,
                'description': habit.description,
                'execution_time': habit.execution_time,
                'frequency': habit.frequency,
                'habit_type': habit.habit_type.value if habit.habit_type else None,
                'reward': habit.reward,
                'related_habit_id': habit.related_habit_id,
                'created_at': habit.created_at.isoformat() if habit.created_at else None,
                'updated_at': habit.updated_at.isoformat() if habit.updated_at else None,
                'is_archived': habit.is_archived
            }
        }), 200
        
    except HabitNotFoundError:
        return jsonify({
            'error': {
                'code': 'HABIT_NOT_FOUND',
                'message': f'Habit with ID {habit_id} not found'
            }
        }), 404
    except AuthorizationError:
        return jsonify({
            'error': {
                'code': 'AUTHORIZATION_ERROR',
                'message': 'You do not have permission to access this habit'
            }
        }), 403
    except Exception as e:
        logger.error(f"Unexpected error getting habit {habit_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@habits_bp.route('/<int:habit_id>', methods=['PUT'])
@login_required
def update_habit(habit_id):
    """
    Update an existing habit
    
    Args:
        habit_id: ID of the habit to update
        
    Expected JSON payload:
    {
        "name": "Updated habit name",
        "description": "Updated description",
        "execution_time": 90,
        "frequency": 2,
        "habit_type": "pleasant",
        "reward": null,
        "related_habit_id": null
    }
    
    Returns:
        JSON response with updated habit data
    """
    try:
        # Validate content type
        if not request.is_json:
            return jsonify({
                'error': {
                    'code': 'INVALID_CONTENT_TYPE',
                    'message': 'Content-Type must be application/json'
                }
            }), 400
        
        habit_data = request.get_json()
        
        if not habit_data:
            return jsonify({
                'error': {
                    'code': 'EMPTY_REQUEST_BODY',
                    'message': 'Request body cannot be empty'
                }
            }), 400
        
        # Convert habit_type string to enum if provided
        if 'habit_type' in habit_data:
            from ..models.habit_types import HabitType
            habit_type_str = habit_data['habit_type']
            if habit_type_str == 'useful':
                habit_data['habit_type'] = HabitType.USEFUL
            elif habit_type_str == 'pleasant':
                habit_data['habit_type'] = HabitType.PLEASANT
            # If it's already an enum, leave it as is
        
        # Update habit using service layer
        habit_service = get_habit_service()
        habit = habit_service.update_habit(habit_id, current_user.id, habit_data)
        
        # Return updated habit
        return jsonify({
            'habit': {
                'id': habit.id,
                'name': habit.name,
                'description': habit.description,
                'execution_time': habit.execution_time,
                'frequency': habit.frequency,
                'habit_type': habit.habit_type.value if habit.habit_type else None,
                'reward': habit.reward,
                'related_habit_id': habit.related_habit_id,
                'created_at': habit.created_at.isoformat() if habit.created_at else None,
                'updated_at': habit.updated_at.isoformat() if habit.updated_at else None,
                'is_archived': habit.is_archived
            }
        }), 200
        
    except HabitNotFoundError:
        return jsonify({
            'error': {
                'code': 'HABIT_NOT_FOUND',
                'message': f'Habit with ID {habit_id} not found'
            }
        }), 404
    except AuthorizationError:
        return jsonify({
            'error': {
                'code': 'AUTHORIZATION_ERROR',
                'message': 'You do not have permission to update this habit'
            }
        }), 403
    except ValidationError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Habit data validation failed',
                'details': [{'message': error} for error in e.errors]
            }
        }), 400
    except HabitServiceError as e:
        logger.error(f"Service error updating habit {habit_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Failed to update habit',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error updating habit {habit_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@habits_bp.route('/<int:habit_id>', methods=['DELETE'])
@login_required
def delete_habit(habit_id):
    """
    Delete a habit
    
    Args:
        habit_id: ID of the habit to delete
        
    Returns:
        Empty response with 204 status code on success
    """
    try:
        # Delete habit using service layer
        habit_service = get_habit_service()
        habit_service.delete_habit(habit_id, current_user.id)
        
        # Return empty response with 204 No Content
        return '', 204
        
    except HabitNotFoundError:
        return jsonify({
            'error': {
                'code': 'HABIT_NOT_FOUND',
                'message': f'Habit with ID {habit_id} not found'
            }
        }), 404
    except AuthorizationError:
        return jsonify({
            'error': {
                'code': 'AUTHORIZATION_ERROR',
                'message': 'You do not have permission to delete this habit'
            }
        }), 403
    except HabitServiceError as e:
        logger.error(f"Service error deleting habit {habit_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Failed to delete habit',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error deleting habit {habit_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@habits_bp.route('/<int:habit_id>/archive', methods=['POST'])
@login_required
def archive_habit(habit_id):
    """
    Archive a habit (soft delete)
    
    Args:
        habit_id: ID of the habit to archive
        
    Returns:
        JSON response with archived habit data
    """
    try:
        # Archive habit using service layer
        habit_service = get_habit_service()
        habit = habit_service.archive_habit(habit_id, current_user.id)
        
        return jsonify({
            'habit': {
                'id': habit.id,
                'name': habit.name,
                'is_archived': habit.is_archived,
                'updated_at': habit.updated_at.isoformat() if habit.updated_at else None
            }
        }), 200
        
    except HabitNotFoundError:
        return jsonify({
            'error': {
                'code': 'HABIT_NOT_FOUND',
                'message': f'Habit with ID {habit_id} not found'
            }
        }), 404
    except AuthorizationError:
        return jsonify({
            'error': {
                'code': 'AUTHORIZATION_ERROR',
                'message': 'You do not have permission to archive this habit'
            }
        }), 403
    except HabitServiceError as e:
        logger.error(f"Service error archiving habit {habit_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Failed to archive habit',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error archiving habit {habit_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@habits_bp.route('/<int:habit_id>/restore', methods=['POST'])
@login_required
def restore_habit(habit_id):
    """
    Restore an archived habit
    
    Args:
        habit_id: ID of the habit to restore
        
    Returns:
        JSON response with restored habit data
    """
    try:
        # Restore habit using service layer
        habit_service = get_habit_service()
        habit = habit_service.restore_habit(habit_id, current_user.id)
        
        return jsonify({
            'habit': {
                'id': habit.id,
                'name': habit.name,
                'is_archived': habit.is_archived,
                'updated_at': habit.updated_at.isoformat() if habit.updated_at else None
            }
        }), 200
        
    except HabitNotFoundError:
        return jsonify({
            'error': {
                'code': 'HABIT_NOT_FOUND',
                'message': f'Habit with ID {habit_id} not found'
            }
        }), 404
    except AuthorizationError:
        return jsonify({
            'error': {
                'code': 'AUTHORIZATION_ERROR',
                'message': 'You do not have permission to restore this habit'
            }
        }), 403
    except HabitServiceError as e:
        logger.error(f"Service error restoring habit {habit_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Failed to restore habit',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error restoring habit {habit_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


# Error handlers for the blueprint
@habits_bp.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors within the habits API"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'The requested resource was not found'
        }
    }), 404


@habits_bp.errorhandler(405)
def handle_method_not_allowed(error):
    """Handle 405 errors within the habits API"""
    return jsonify({
        'error': {
            'code': 'METHOD_NOT_ALLOWED',
            'message': 'The requested method is not allowed for this resource'
        }
    }), 405
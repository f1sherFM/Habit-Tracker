"""
Users API Endpoints

RESTful API for user management using UserService for business logic
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..services.user_service import (
    UserService, AuthenticationError, UserNotFoundError, 
    UserAlreadyExistsError, UserServiceError
)
import logging

# Create blueprint
users_bp = Blueprint('users_api', __name__, url_prefix='/api/users')

# Service will be initialized when needed
user_service = None

def get_user_service():
    """Get or create UserService instance"""
    global user_service
    if user_service is None:
        user_service = UserService()
    return user_service

logger = logging.getLogger(__name__)


@users_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """
    Get current user profile information
    
    Returns:
        JSON response with user data
    """
    try:
        # Get user statistics using service layer
        user_service = get_user_service()
        user_stats = user_service.get_user_statistics(current_user.id)
        
        return jsonify({
            'user': {
                'id': current_user.id,
                'email': current_user.email,
                'name': current_user.name,
                'avatar_url': current_user.avatar_url,
                'default_tracking_days': current_user.default_tracking_days or 7,
                'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
                'updated_at': current_user.updated_at.isoformat() if current_user.updated_at else None,
                'is_active': current_user.is_active,
                'statistics': user_stats
            }
        }), 200
        
    except UserServiceError as e:
        logger.error(f"Service error getting user profile for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Failed to retrieve user profile',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting user profile for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@users_bp.route('/me', methods=['PUT'])
@login_required
def update_current_user():
    """
    Update current user profile information
    
    Expected JSON payload:
    {
        "name": "Updated name",
        "avatar_url": "https://example.com/avatar.jpg",
        "default_tracking_days": 14
    }
    
    Returns:
        JSON response with updated user data
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
        
        user_data = request.get_json()
        
        if not user_data:
            return jsonify({
                'error': {
                    'code': 'EMPTY_REQUEST_BODY',
                    'message': 'Request body cannot be empty'
                }
            }), 400
        
        # Validate default_tracking_days if provided
        if 'default_tracking_days' in user_data:
            tracking_days = user_data.get('default_tracking_days')
            if not isinstance(tracking_days, int) or tracking_days < 1 or tracking_days > 30:
                return jsonify({
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'default_tracking_days must be an integer between 1 and 30'
                    }
                }), 400
        
        # Update user using service layer
        user_service = get_user_service()
        updated_user = user_service.update_user(current_user.id, user_data)
        
        return jsonify({
            'user': {
                'id': updated_user.id,
                'email': updated_user.email,
                'name': updated_user.name,
                'avatar_url': updated_user.avatar_url,
                'default_tracking_days': updated_user.default_tracking_days or 7,
                'updated_at': updated_user.updated_at.isoformat() if updated_user.updated_at else None
            }
        }), 200
        
    except UserServiceError as e:
        logger.error(f"Service error updating user profile for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Failed to update user profile',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error updating user profile for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@users_bp.route('/me/password', methods=['PUT'])
@login_required
def change_password():
    """
    Change current user password
    
    Expected JSON payload:
    {
        "current_password": "current_password",
        "new_password": "new_password"
    }
    
    Returns:
        JSON response confirming password change
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
        
        password_data = request.get_json()
        
        # Validate required fields
        if not password_data or not password_data.get('current_password') or not password_data.get('new_password'):
            return jsonify({
                'error': {
                    'code': 'MISSING_REQUIRED_FIELDS',
                    'message': 'Both current_password and new_password are required'
                }
            }), 400
        
        # Change password using service layer
        user_service = get_user_service()
        success = user_service.change_password(
            current_user.id,
            password_data['current_password'],
            password_data['new_password']
        )
        
        if success:
            return jsonify({
                'message': 'Password changed successfully'
            }), 200
        else:
            return jsonify({
                'error': {
                    'code': 'PASSWORD_CHANGE_FAILED',
                    'message': 'Failed to change password'
                }
            }), 500
        
    except AuthenticationError as e:
        return jsonify({
            'error': {
                'code': 'AUTHENTICATION_ERROR',
                'message': str(e)
            }
        }), 400
    except UserServiceError as e:
        logger.error(f"Service error changing password for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Failed to change password',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error changing password for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@users_bp.route('/me/deactivate', methods=['POST'])
@login_required
def deactivate_account():
    """
    Deactivate current user account
    
    Returns:
        JSON response confirming account deactivation
    """
    try:
        # Deactivate user using service layer
        user_service = get_user_service()
        deactivated_user = user_service.deactivate_user(current_user.id)
        
        return jsonify({
            'message': 'Account deactivated successfully',
            'user': {
                'id': deactivated_user.id,
                'is_active': deactivated_user.is_active,
                'updated_at': deactivated_user.updated_at.isoformat() if deactivated_user.updated_at else None
            }
        }), 200
        
    except UserServiceError as e:
        logger.error(f"Service error deactivating account for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Failed to deactivate account',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error deactivating account for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@users_bp.route('/me/statistics', methods=['GET'])
@login_required
def get_user_statistics():
    """
    Get detailed statistics for current user
    
    Returns:
        JSON response with user statistics
    """
    try:
        # Get user statistics using service layer
        user_service = get_user_service()
        stats = user_service.get_user_statistics(current_user.id)
        
        return jsonify({
            'statistics': stats
        }), 200
        
    except UserServiceError as e:
        logger.error(f"Service error getting statistics for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Failed to retrieve user statistics',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting statistics for user {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


# Error handlers for the blueprint
@users_bp.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors within the users API"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'The requested resource was not found'
        }
    }), 404


@users_bp.errorhandler(405)
def handle_method_not_allowed(error):
    """Handle 405 errors within the users API"""
    return jsonify({
        'error': {
            'code': 'METHOD_NOT_ALLOWED',
            'message': 'The requested method is not allowed for this resource'
        }
    }), 405
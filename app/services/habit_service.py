"""
Habit Service

Business logic layer for habit management with validation and authorization
"""
from typing import List, Optional, Tuple, Union
from datetime import datetime, timezone
from ..validators.habit_validator import HabitValidator
from ..models import get_models
from ..exceptions import (
    ValidationError, AuthorizationError, ResourceNotFoundError,
    BusinessLogicError, HabitTrackerException
)


class HabitServiceError(HabitTrackerException):
    """Base exception for HabitService errors"""
    pass


class HabitNotFoundError(ResourceNotFoundError):
    """Raised when habit is not found"""
    def __init__(self, habit_id: int):
        super().__init__('habit', habit_id)


class HabitService:
    """
    Service layer for habit management with business logic, validation, and authorization
    """
    
    def __init__(self, habit_validator: HabitValidator = None):
        """
        Initialize HabitService
        
        Args:
            habit_validator: Validator for habit data (optional, will create default if None)
        """
        self.habit_validator = habit_validator or HabitValidator()
        # Get models after initialization
        self.User, self.Habit, self.HabitLog = get_models()
        
        # Import db from models
        from ..models.habit import db
        self.db = db
    
    def create_habit(self, user_id: int, habit_data: dict) -> 'Habit':
        """
        Create a new habit with validation
        
        Args:
            user_id: ID of the user creating the habit
            habit_data: Dictionary containing habit data
            
        Returns:
            Habit: Created habit instance
            
        Raises:
            ValidationError: If habit data is invalid
            HabitServiceError: If creation fails
        """
        # Validate input data
        validation_result = self.habit_validator.validate(habit_data)
        if not validation_result.is_valid:
            raise ValidationError(validation_result.errors)
        
        try:
            # Create habit instance
            habit_data['user_id'] = user_id
            habit = self.Habit(**habit_data)
            
            # Additional business rule validation at model level
            is_valid, errors = habit.validate_business_rules()
            if not is_valid:
                raise ValidationError(errors)
            
            # Save to database
            self.db.session.add(habit)
            self.db.session.commit()
            
            return habit
            
        except Exception as e:
            self.db.session.rollback()
            if isinstance(e, (ValidationError, HabitServiceError)):
                raise
            raise HabitServiceError(f"Failed to create habit: {str(e)}")
    
    def update_habit(self, habit_id: int, user_id: int, habit_data: dict) -> 'Habit':
        """
        Update an existing habit with authorization and validation
        
        Args:
            habit_id: ID of the habit to update
            user_id: ID of the user requesting the update
            habit_data: Dictionary containing updated habit data
            
        Returns:
            Habit: Updated habit instance
            
        Raises:
            HabitNotFoundError: If habit doesn't exist
            AuthorizationError: If user doesn't own the habit
            ValidationError: If updated data is invalid
            HabitServiceError: If update fails
        """
        # Find habit
        habit = self.Habit.query.get(habit_id)
        if not habit:
            raise HabitNotFoundError(habit_id)
        
        # Check authorization
        if habit.user_id != user_id:
            raise AuthorizationError("User does not have permission to update this habit", 'habit', 'update')
        
        # Validate input data
        validation_result = self.habit_validator.validate(habit_data)
        if not validation_result.is_valid:
            raise ValidationError(validation_result.errors)
        
        try:
            # Update habit with validation
            is_valid, errors = habit.update_with_validation(**habit_data)
            if not is_valid:
                raise ValidationError(errors)
            
            # Update timestamp
            habit.updated_at = datetime.now(timezone.utc)
            
            # Save to database
            self.db.session.commit()
            
            return habit
            
        except Exception as e:
            self.db.session.rollback()
            if isinstance(e, (ValidationError, AuthorizationError, HabitServiceError)):
                raise
            raise HabitServiceError(f"Failed to update habit: {str(e)}")
    
    def delete_habit(self, habit_id: int, user_id: int) -> bool:
        """
        Delete a habit with authorization and cascade deletion of related records
        
        Args:
            habit_id: ID of the habit to delete
            user_id: ID of the user requesting the deletion
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            HabitNotFoundError: If habit doesn't exist
            AuthorizationError: If user doesn't own the habit
            HabitServiceError: If deletion fails
        """
        # Find habit
        habit = self.Habit.query.get(habit_id)
        if not habit:
            raise HabitNotFoundError(habit_id)
        
        # Check authorization
        if habit.user_id != user_id:
            raise AuthorizationError("User does not have permission to delete this habit", 'habit', 'delete')
        
        try:
            # Delete related records (cascade deletion)
            # 1. Delete habit logs
            self.HabitLog.query.filter_by(habit_id=habit_id).delete()
            
            # 2. Update related habits to remove references
            related_habits = self.Habit.query.filter_by(related_habit_id=habit_id).all()
            for related_habit in related_habits:
                related_habit.related_habit_id = None
            
            # 3. Delete the habit itself
            self.db.session.delete(habit)
            self.db.session.commit()
            
            return True
            
        except Exception as e:
            self.db.session.rollback()
            if isinstance(e, (AuthorizationError, HabitServiceError)):
                raise
            raise HabitServiceError(f"Failed to delete habit: {str(e)}")
    
    def get_user_habits(self, user_id: int, include_archived: bool = False) -> List['Habit']:
        """
        Get all habits for a user
        
        Args:
            user_id: ID of the user
            include_archived: Whether to include archived habits (default: False)
            
        Returns:
            List[Habit]: List of user's habits
            
        Raises:
            HabitServiceError: If retrieval fails
        """
        try:
            query = self.Habit.query.filter_by(user_id=user_id)
            
            if not include_archived:
                query = query.filter_by(is_archived=False)
            
            habits = query.order_by(self.Habit.created_at.desc()).all()
            return habits
            
        except Exception as e:
            raise HabitServiceError(f"Failed to retrieve user habits: {str(e)}")
    
    def get_habit_by_id(self, habit_id: int, user_id: int) -> 'Habit':
        """
        Get a specific habit by ID with authorization check
        
        Args:
            habit_id: ID of the habit
            user_id: ID of the user requesting the habit
            
        Returns:
            Habit: The requested habit
            
        Raises:
            HabitNotFoundError: If habit doesn't exist
            AuthorizationError: If user doesn't own the habit
        """
        habit = self.Habit.query.get(habit_id)
        if not habit:
            raise HabitNotFoundError(habit_id)
        
        if habit.user_id != user_id:
            raise AuthorizationError("User does not have permission to access this habit", 'habit', 'read')
        
        return habit
    
    def archive_habit(self, habit_id: int, user_id: int) -> 'Habit':
        """
        Archive a habit (soft delete)
        
        Args:
            habit_id: ID of the habit to archive
            user_id: ID of the user requesting the archive
            
        Returns:
            Habit: Archived habit instance
            
        Raises:
            HabitNotFoundError: If habit doesn't exist
            AuthorizationError: If user doesn't own the habit
            HabitServiceError: If archiving fails
        """
        habit = self.get_habit_by_id(habit_id, user_id)
        
        try:
            habit.is_archived = True
            habit.updated_at = datetime.now(timezone.utc)
            self.db.session.commit()
            
            return habit
            
        except Exception as e:
            self.db.session.rollback()
            raise HabitServiceError(f"Failed to archive habit: {str(e)}")
    
    def restore_habit(self, habit_id: int, user_id: int) -> 'Habit':
        """
        Restore an archived habit
        
        Args:
            habit_id: ID of the habit to restore
            user_id: ID of the user requesting the restore
            
        Returns:
            Habit: Restored habit instance
            
        Raises:
            HabitNotFoundError: If habit doesn't exist
            AuthorizationError: If user doesn't own the habit
            HabitServiceError: If restoration fails
        """
        # Get habit including archived ones
        habit = self.Habit.query.get(habit_id)
        if not habit:
            raise HabitNotFoundError(habit_id)
        
        if habit.user_id != user_id:
            raise AuthorizationError("User does not have permission to restore this habit", 'habit', 'restore')
        
        try:
            habit.is_archived = False
            habit.updated_at = datetime.now(timezone.utc)
            self.db.session.commit()
            
            return habit
            
        except Exception as e:
            self.db.session.rollback()
            raise HabitServiceError(f"Failed to restore habit: {str(e)}")
    
    def get_habits_by_type(self, user_id: int, habit_type: str) -> List['Habit']:
        """
        Get habits of a specific type for a user
        
        Args:
            user_id: ID of the user
            habit_type: Type of habits to retrieve ('useful' or 'pleasant')
            
        Returns:
            List[Habit]: List of habits of the specified type
            
        Raises:
            HabitServiceError: If retrieval fails
        """
        try:
            from ..models.habit_types import HabitType
            
            # Convert string to enum
            if habit_type == 'useful':
                type_enum = HabitType.USEFUL
            elif habit_type == 'pleasant':
                type_enum = HabitType.PLEASANT
            else:
                raise HabitServiceError(f"Invalid habit type: {habit_type}")
            
            habits = self.Habit.query.filter_by(
                user_id=user_id,
                habit_type=type_enum,
                is_archived=False
            ).order_by(self.Habit.created_at.desc()).all()
            
            return habits
            
        except Exception as e:
            if isinstance(e, HabitServiceError):
                raise
            raise HabitServiceError(f"Failed to retrieve habits by type: {str(e)}")
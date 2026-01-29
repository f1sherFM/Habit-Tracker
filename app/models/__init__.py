"""
Data Models Package

Enhanced models with new fields and business logic
"""

# Global model classes - will be set after initialization
User = None
Habit = None
HabitLog = None
Category = None
Tag = None
Comment = None
habit_tags = None

# Track if models have been initialized
_models_initialized = False

def init_db(database):
    """Initialize models with database instance"""
    global User, Habit, HabitLog, Category, Tag, Comment, habit_tags, _models_initialized
    
    # Only initialize once
    if _models_initialized:
        return
    
    # Import all model modules and create model classes
    from . import habit_types
    from . import user
    from . import habit
    from . import habit_log
    from . import category
    from . import tag
    from . import comment
    
    # Create model classes with database instance
    User = user.create_user_model(database)
    Habit = habit.create_habit_model(database)
    HabitLog = habit_log.create_habit_log_model(database)
    Category = category.create_category_model(database)
    Tag, habit_tags = tag.create_tag_model(database)
    Comment = comment.create_comment_model(database)
    
    # Set the global references in modules
    user.User = User
    habit.Habit = Habit
    habit_log.HabitLog = HabitLog
    category.Category = Category
    tag.Tag = Tag
    tag.habit_tags = habit_tags
    comment.Comment = Comment
    
    # Mark as initialized
    _models_initialized = True

# Import models after db initialization
from .habit_types import HabitType

def get_models():
    """Get model classes after initialization"""
    if not _models_initialized:
        raise RuntimeError("Models not initialized. Call init_db() first.")
    return User, Habit, HabitLog, Category, Tag, Comment

def reset_models():
    """Reset models for testing purposes"""
    global User, Habit, HabitLog, Category, Tag, Comment, habit_tags, _models_initialized
    User = None
    Habit = None
    HabitLog = None
    Category = None
    Tag = None
    Comment = None
    habit_tags = None
    _models_initialized = False

__all__ = [
    'HabitType',
    'init_db',
    'get_models',
    'reset_models',
    'User',
    'Habit', 
    'HabitLog',
    'Category',
    'Tag',
    'Comment'
]
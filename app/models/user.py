"""
User Model

Enhanced user model for authentication and habit management
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

# This will be initialized by the app factory
db = None


def create_user_model(database):
    """Create User model with database instance"""
    global db
    db = database
    
    class User(UserMixin, db.Model):
        """
        User model for authentication and habit management
        """
        __tablename__ = 'users'
        
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(120), unique=True, nullable=False, index=True)
        password_hash = db.Column(db.String(255))  # Increased length for better security
        google_id = db.Column(db.String(50), unique=True, index=True)
        github_id = db.Column(db.String(50), unique=True, index=True)
        name = db.Column(db.String(100))
        avatar_url = db.Column(db.String(500))  # Increased length for URLs
        created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
        updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                              onupdate=lambda: datetime.now(timezone.utc))
        is_active = db.Column(db.Boolean, default=True)
        
        # Advanced features fields
        default_tracking_days = db.Column(db.Integer, default=7)  # Период отслеживания по умолчанию
        
        # Relationship to habits
        habits = db.relationship('Habit', backref='user', lazy=True, cascade='all, delete-orphan')
        
        def __repr__(self):
            return f'<User {self.email}>'
        
        def set_password(self, password):
            """
            Set user password with enhanced security validation and hashing.
            
            Args:
                password: The plain text password to set
                
            Raises:
                ValueError: If password doesn't meet security requirements
            """
            # Import here to avoid circular imports
            try:
                from password_security import PasswordValidator, SecurePasswordHasher
                
                # Validate password strength
                is_valid, errors = PasswordValidator.validate_password_strength(password)
                if not is_valid:
                    raise ValueError(f"Password security requirements not met: {'; '.join(errors)}")
                
                # Hash password with secure method
                self.password_hash = SecurePasswordHasher.hash_password(password)
            except ImportError:
                # Fallback to basic hashing if password_security module not available
                self.password_hash = generate_password_hash(password)
        
        def check_password(self, password):
            """
            Check if provided password matches the stored hash.
            Also checks if password hash needs updating to current security standards.
            
            Args:
                password: The plain text password to verify
                
            Returns:
                bool: True if password matches
            """
            if not self.password_hash:
                return False
            
            try:
                # Import here to avoid circular imports
                from password_security import SecurePasswordHasher
                
                # Verify password
                is_valid = SecurePasswordHasher.verify_password(password, self.password_hash)
                
                # Check if hash needs updating (rehash with stronger parameters if needed)
                if is_valid and SecurePasswordHasher.needs_rehash(self.password_hash):
                    try:
                        # Update to current security standards
                        self.password_hash = SecurePasswordHasher.hash_password(password)
                        # Note: The calling code should commit this change to the database
                    except Exception:
                        # If rehashing fails, continue with the valid login
                        pass
                
                return is_valid
            except ImportError:
                # Fallback to basic verification if password_security module not available
                return check_password_hash(self.password_hash, password)
        
        @staticmethod
        def get_or_create_from_google(google_user):
            """
            Get or create user from Google OAuth data
            
            Args:
                google_user: Google user data
                
            Returns:
                User: User instance
            """
            user = User.query.filter_by(google_id=google_user['id']).first()
            if not user:
                user = User.query.filter_by(email=google_user['email']).first()
                if user:
                    user.google_id = google_user['id']
                else:
                    user = User(
                        email=google_user['email'],
                        google_id=google_user['id'],
                        name=google_user.get('name'),
                        avatar_url=google_user.get('picture')
                    )
                    db.session.add(user)
            db.session.commit()
            return user
        
        @staticmethod
        def get_or_create_from_github(github_user):
            """
            Get or create user from GitHub OAuth data
            
            Args:
                github_user: GitHub user data
                
            Returns:
                User: User instance
            """
            user = User.query.filter_by(github_id=str(github_user['id'])).first()
            if not user:
                user = User.query.filter_by(email=github_user['email']).first()
                if user:
                    user.github_id = str(github_user['id'])
                else:
                    user = User(
                        email=github_user.get('email') or f"{github_user['login']}@github.local",
                        github_id=str(github_user['id']),
                        name=github_user.get('name') or github_user['login'],
                        avatar_url=github_user.get('avatar_url')
                    )
                    db.session.add(user)
            db.session.commit()
            return user
        
        def get_active_habits(self):
            """
            Get all active (non-archived) habits for this user
            
            Returns:
                List[Habit]: List of active habits
            """
            return [habit for habit in self.habits if not habit.is_archived]
        
        def get_habits_by_type(self, habit_type):
            """
            Get habits of a specific type
            
            Args:
                habit_type: HabitType enum value
                
            Returns:
                List[Habit]: List of habits of the specified type
            """
            return [habit for habit in self.get_active_habits() if habit.habit_type == habit_type]
        
        def get_completion_stats(self):
            """
            Get completion statistics for this user
            
            Returns:
                dict: Statistics including total habits, completion rates, etc.
            """
            active_habits = self.get_active_habits()
            
            if not active_habits:
                return {
                    'total_habits': 0,
                    'average_completion_rate': 0,
                    'habits_completed_today': 0,
                    'streak_count': 0
                }
            
            total_habits = len(active_habits)
            completion_rates = [habit.get_completion_rate() for habit in active_habits]
            average_completion_rate = sum(completion_rates) / len(completion_rates)
            
            # Count habits that can be completed today and are completed
            today = datetime.now(timezone.utc).date()
            habits_completed_today = 0
            
            for habit in active_habits:
                if habit.can_be_completed_today():
                    # Import here to avoid circular imports
                    from .habit_log import HabitLog
                    log = HabitLog.query.filter_by(
                        habit_id=habit.id,
                        date=today,
                        completed=True
                    ).first()
                    if log:
                        habits_completed_today += 1
            
            return {
                'total_habits': total_habits,
                'average_completion_rate': round(average_completion_rate, 1),
                'habits_completed_today': habits_completed_today,
                'habits_due_today': len([h for h in active_habits if h.can_be_completed_today()])
            }
        
        def to_dict(self):
            """
            Convert user to dictionary for API responses
            
            Returns:
                dict: User data as dictionary (excluding sensitive information)
            """
            return {
                'id': self.id,
                'email': self.email,
                'name': self.name,
                'avatar_url': self.avatar_url,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'is_active': self.is_active,
                'stats': self.get_completion_stats()
            }
    
    return User


# Global User class - will be set after initialization
User = None
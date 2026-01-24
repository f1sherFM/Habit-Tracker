"""
Habit Model

Enhanced habit model with new fields for improved tracking
"""
from datetime import datetime, timezone, timedelta
from .habit_types import HabitType

# This will be initialized by the app factory
db = None


def create_habit_model(database):
    """Create Habit model with database instance"""
    global db
    db = database
    
    class Habit(db.Model):
        """
        Enhanced Habit model with new fields for comprehensive habit tracking
        """
        __tablename__ = 'habits'
        
        # Core fields
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
        name = db.Column(db.String(100), nullable=False)
        description = db.Column(db.Text, nullable=True)
        
        # New enhanced fields
        execution_time = db.Column(db.Integer, default=60, nullable=False)  # Time in seconds
        frequency = db.Column(db.Integer, default=1, nullable=False)        # Frequency in days
        habit_type = db.Column(db.Enum(HabitType), default=HabitType.USEFUL, nullable=False)
        reward = db.Column(db.String(200), nullable=True)                   # Reward for useful habits
        related_habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=True)
        
        # Metadata fields
        created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
        updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                              onupdate=lambda: datetime.now(timezone.utc))
        is_archived = db.Column(db.Boolean, default=False)
        
        # Relationships
        logs = db.relationship('HabitLog', backref='habit', lazy=True, cascade='all, delete-orphan')
        related_habit = db.relationship('Habit', remote_side=[id], backref='related_habits')
        
        # Indexes for performance
        __table_args__ = (
            db.Index('idx_habits_user_type', 'user_id', 'habit_type'),
            db.Index('idx_habits_frequency', 'frequency'),
            db.Index('idx_habits_related', 'related_habit_id'),
        )
        
        def __repr__(self):
            return f'<Habit {self.name} ({self.habit_type.value})>'
        
        def validate_business_rules(self):
            """
            Validate business rules for habit creation/update
            
            Returns:
                tuple: (is_valid: bool, errors: List[str])
            """
            errors = []
            
            # Rule 1: Pleasant habits cannot have rewards
            if self.habit_type == HabitType.PLEASANT and self.reward:
                errors.append("Приятная привычка не может иметь вознаграждение")
            
            # Rule 2: Pleasant habits cannot be related to other habits
            if self.habit_type == HabitType.PLEASANT and self.related_habit_id:
                errors.append("Приятная привычка не может быть связана с другой привычкой")
            
            # Rule 3: Useful habits can have either reward OR related habit, but not both
            if (self.habit_type == HabitType.USEFUL and 
                self.reward and self.related_habit_id):
                errors.append("Полезная привычка может иметь либо вознаграждение, либо связанную привычку, но не оба")
            
            # Rule 4: Execution time must be <= 120 seconds
            if self.execution_time and self.execution_time > 120:
                errors.append("Время выполнения не может превышать 120 секунд")
            
            # Rule 5: Frequency must be >= 7 days
            if self.frequency and self.frequency < 7:
                errors.append("Периодичность не может быть чаще чем раз в 7 дней")
            
            # Rule 6: Name cannot be empty
            if not self.name or not self.name.strip():
                errors.append("Название привычки не может быть пустым")
            
            # Rule 7: Reward length limit
            if self.reward and len(self.reward) > 200:
                errors.append("Вознаграждение не может превышать 200 символов")
            
            return len(errors) == 0, errors
        
        def get_last_7_days(self):
            """
            Get the completion status for the last 7 days
            Returns a list of dictionaries with date and completion status
            """
            today = datetime.now(timezone.utc).date()
            last_7_days = []
            
            for i in range(6, -1, -1):
                date = today - timedelta(days=i)
                
                # Import here to avoid circular imports
                from .habit_log import HabitLog
                log = HabitLog.query.filter_by(
                    habit_id=self.id,
                    date=date
                ).first()
                
                last_7_days.append({
                    'date': date,
                    'completed': log.completed if log else False,
                    'date_str': date.strftime('%b %d')
                })
            
            return last_7_days
        
        def get_completion_rate(self):
            """
            Calculate the completion rate for the last 7 days
            """
            days = self.get_last_7_days()
            completed = sum(1 for day in days if day['completed'])
            return int((completed / 7) * 100)
        
        def can_be_completed_today(self):
            """
            Check if this habit can be completed today based on its frequency
            
            Returns:
                bool: True if habit can be completed today
            """
            if not self.frequency:
                return True  # Default to daily if no frequency set
            
            today = datetime.now(timezone.utc).date()
            
            # Import here to avoid circular imports
            from .habit_log import HabitLog
            
            # Find the last completion
            last_log = HabitLog.query.filter_by(
                habit_id=self.id,
                completed=True
            ).order_by(HabitLog.date.desc()).first()
            
            if not last_log:
                return True  # Never completed, can be done today
            
            # Check if enough days have passed
            days_since_last = (today - last_log.date).days
            return days_since_last >= self.frequency
        
        def get_next_due_date(self):
            """
            Get the next date when this habit is due
            
            Returns:
                date: Next due date or None if can be done today
            """
            if self.can_be_completed_today():
                return datetime.now(timezone.utc).date()
            
            # Import here to avoid circular imports
            from .habit_log import HabitLog
            
            last_log = HabitLog.query.filter_by(
                habit_id=self.id,
                completed=True
            ).order_by(HabitLog.date.desc()).first()
            
            if last_log:
                return last_log.date + timedelta(days=self.frequency)
            
            return datetime.now(timezone.utc).date()
        
        def is_pleasant_habit(self):
            """Check if this is a pleasant habit"""
            return self.habit_type == HabitType.PLEASANT
        
        def is_useful_habit(self):
            """Check if this is a useful habit"""
            return self.habit_type == HabitType.USEFUL
        
        def has_reward(self):
            """Check if this habit has a reward"""
            return bool(self.reward and self.reward.strip())
        
        def has_related_habit(self):
            """Check if this habit is related to another habit"""
            return self.related_habit_id is not None
        
        def get_execution_time_minutes(self):
            """Get execution time in minutes"""
            return self.execution_time / 60 if self.execution_time else 1
        
        def get_frequency_description(self):
            """Get human-readable frequency description"""
            if not self.frequency:
                return "Ежедневно"
            elif self.frequency == 1:
                return "Ежедневно"
            elif self.frequency == 7:
                return "Еженедельно"
            elif self.frequency == 30:
                return "Ежемесячно"
            else:
                return f"Каждые {self.frequency} дней"
        
        def to_dict(self):
            """
            Convert habit to dictionary for API responses
            
            Returns:
                dict: Habit data as dictionary
            """
            return {
                'id': self.id,
                'user_id': self.user_id,
                'name': self.name,
                'description': self.description,
                'execution_time': self.execution_time,
                'frequency': self.frequency,
                'habit_type': self.habit_type.value if self.habit_type else 'useful',
                'reward': self.reward,
                'related_habit_id': self.related_habit_id,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'is_archived': self.is_archived,
                'completion_rate': self.get_completion_rate(),
                'can_complete_today': self.can_be_completed_today(),
                'next_due_date': self.get_next_due_date().isoformat() if self.get_next_due_date() else None,
                'execution_time_minutes': self.get_execution_time_minutes(),
                'frequency_description': self.get_frequency_description()
            }
        
        @classmethod
        def create_with_validation(cls, **kwargs):
            """
            Create a new habit with business rule validation
            
            Args:
                **kwargs: Habit attributes
                
            Returns:
                tuple: (habit: Habit, is_valid: bool, errors: List[str])
            """
            habit = cls(**kwargs)
            is_valid, errors = habit.validate_business_rules()
            return habit, is_valid, errors
        
        def update_with_validation(self, **kwargs):
            """
            Update habit with business rule validation
            
            Args:
                **kwargs: Attributes to update
                
            Returns:
                tuple: (is_valid: bool, errors: List[str])
            """
            # Store original values for rollback
            original_values = {}
            for key, value in kwargs.items():
                if hasattr(self, key):
                    original_values[key] = getattr(self, key)
                    setattr(self, key, value)
            
            # Validate
            is_valid, errors = self.validate_business_rules()
            
            # Rollback if invalid
            if not is_valid:
                for key, value in original_values.items():
                    setattr(self, key, value)
            
            return is_valid, errors
    
    return Habit


# Global Habit class - will be set after initialization
Habit = None
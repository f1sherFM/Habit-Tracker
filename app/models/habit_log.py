"""
Habit Log Model

Model for tracking daily completion status for each habit
"""
from datetime import datetime, timezone

# This will be initialized by the app factory
db = None


def create_habit_log_model(database):
    """Create HabitLog model with database instance"""
    global db
    db = database
    
    class HabitLog(db.Model):
        """
        HabitLog model tracking daily completion status for each habit
        """
        __tablename__ = 'habit_logs'
        
        id = db.Column(db.Integer, primary_key=True)
        habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False, index=True)
        date = db.Column(db.Date, nullable=False, index=True)
        completed = db.Column(db.Boolean, default=False)
        notes = db.Column(db.Text, nullable=True)
        duration = db.Column(db.Integer, nullable=True)  # Actual duration in seconds
        created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
        
        # Ensure one log per habit per date and optimize foreign key relationships
        __table_args__ = (
            db.UniqueConstraint('habit_id', 'date', name='unique_habit_date'),
            db.Index('idx_habit_date', 'habit_id', 'date'),
        )
        
        def __repr__(self):
            return f'<HabitLog {self.habit_id} - {self.date}: {self.completed}>'
        
        def to_dict(self):
            """
            Convert habit log to dictionary for API responses
            
            Returns:
                dict: Habit log data as dictionary
            """
            return {
                'id': self.id,
                'habit_id': self.habit_id,
                'date': self.date.isoformat() if self.date else None,
                'completed': self.completed,
                'notes': self.notes,
                'duration': self.duration,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
        
        @classmethod
        def get_or_create(cls, habit_id, date):
            """
            Get existing log or create new one for habit and date
            
            Args:
                habit_id: ID of the habit
                date: Date for the log
                
            Returns:
                HabitLog: Existing or new habit log
            """
            log = cls.query.filter_by(habit_id=habit_id, date=date).first()
            if not log:
                log = cls(habit_id=habit_id, date=date, completed=False)
                db.session.add(log)
            return log
        
        def toggle_completion(self):
            """
            Toggle the completion status of this log
            
            Returns:
                bool: New completion status
            """
            self.completed = not self.completed
            return self.completed
    
    return HabitLog


# Global HabitLog class - will be set after initialization
HabitLog = None
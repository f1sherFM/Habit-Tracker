"""
Модель Комментарий

Модель для добавления комментариев к выполнению привычек
"""
from datetime import datetime, timezone

# Это будет инициализировано фабрикой приложения
db = None


def create_comment_model(database):
    """Создать модель Comment с экземпляром базы данных"""
    global db
    db = database
    
    class Comment(db.Model):
        """
        Модель комментария для отслеживания заметок о выполнении привычек
        """
        __tablename__ = 'comments'
        
        id = db.Column(db.Integer, primary_key=True)
        habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False, index=True)
        habit_log_id = db.Column(db.Integer, db.ForeignKey('habit_logs.id'), nullable=False, index=True)
        text = db.Column(db.String(500), nullable=False)
        created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
        updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                              onupdate=lambda: datetime.now(timezone.utc))
        
        # Связи
        habit = db.relationship('Habit', backref='comments')
        habit_log = db.relationship('HabitLog', backref='comments')
        
        # Индексы
        __table_args__ = (
            db.Index('idx_habit_log_comments', 'habit_log_id'),
            db.Index('idx_habit_comments', 'habit_id'),
        )
        
        def __repr__(self):
            return f'<Comment {self.id} for HabitLog {self.habit_log_id}>'
        
        def to_dict(self):
            """
            Преобразовать комментарий в словарь для API ответов
            
            Returns:
                dict: Данные комментария в виде словаря
            """
            return {
                'id': self.id,
                'habit_id': self.habit_id,
                'habit_log_id': self.habit_log_id,
                'text': self.text,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'is_edited': self.created_at != self.updated_at if self.created_at and self.updated_at else False
            }
    
    return Comment


# Глобальный класс Comment - будет установлен после инициализации
Comment = None

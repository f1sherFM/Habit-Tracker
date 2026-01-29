"""
Модель Тег

Модель для добавления тегов к привычкам
"""
from datetime import datetime, timezone

# Это будет инициализировано фабрикой приложения
db = None


def create_tag_model(database):
    """Создать модель Tag с экземпляром базы данных"""
    global db
    db = database
    
    # Таблица связей для отношения многие-ко-многим
    habit_tags = db.Table('habit_tags',
        db.Column('habit_id', db.Integer, db.ForeignKey('habits.id'), primary_key=True),
        db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
    )
    
    class Tag(db.Model):
        """
        Модель тега для организации привычек
        """
        __tablename__ = 'tags'
        
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
        name = db.Column(db.String(20), nullable=False)
        created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
        
        # Связи
        habits = db.relationship('Habit', secondary=habit_tags, backref='tags')
        user = db.relationship('User', backref='tags')
        
        # Индексы и ограничения
        __table_args__ = (
            db.UniqueConstraint('user_id', 'name', name='unique_user_tag'),
            db.Index('idx_tags_user', 'user_id'),
        )
        
        def __repr__(self):
            return f'<Tag {self.name}>'
        
        def to_dict(self):
            """
            Преобразовать тег в словарь для API ответов
            
            Returns:
                dict: Данные тега в виде словаря
            """
            return {
                'id': self.id,
                'user_id': self.user_id,
                'name': self.name,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'habits_count': len(self.habits)
            }
    
    return Tag, habit_tags


# Глобальный класс Tag - будет установлен после инициализации
Tag = None
habit_tags = None

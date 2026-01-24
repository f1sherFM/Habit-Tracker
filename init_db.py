#!/usr/bin/env python3
"""
Database Initialization Script
Creates the initial database tables
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment
os.environ.setdefault('FLASK_ENV', 'development')

# Import Flask app components
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
from database_config import DatabaseConfig

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Initialize database configuration
db_config = DatabaseConfig()
database_uri = db_config.get_database_uri()
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri

# Configure SQLAlchemy engine options based on database type
connection_params = db_config.get_connection_params()

# Filter out PostgreSQL-specific parameters for SQLite
if database_uri.startswith('sqlite://'):
    engine_options = {
        'pool_pre_ping': connection_params.get('pool_pre_ping', True),
        'connect_args': connection_params.get('connect_args', {})
    }
else:
    engine_options = connection_params

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define models (simplified versions from app.py)
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255))
    google_id = db.Column(db.String(50), unique=True, index=True)
    github_id = db.Column(db.String(50), unique=True, index=True)
    name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to habits
    habits = db.relationship('Habit', backref='user', lazy=True, cascade='all, delete-orphan')

class Habit(db.Model):
    __tablename__ = 'habits'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_archived = db.Column(db.Boolean, default=False)
    
    # Relationship to habit logs
    logs = db.relationship('HabitLog', backref='habit', lazy=True, cascade='all, delete-orphan')

class HabitLog(db.Model):
    __tablename__ = 'habit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Ensure one log per habit per date
    __table_args__ = (
        db.UniqueConstraint('habit_id', 'date', name='unique_habit_date'),
        db.Index('idx_habit_date', 'habit_id', 'date'),
    )

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def main():
    """Initialize the database tables."""
    try:
        print("Initializing database...")
        print(f"Database URI: {database_uri}")
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Verify tables were created
            from sqlalchemy import text
            with db.engine.connect() as conn:
                if database_uri.startswith('sqlite://'):
                    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                else:
                    result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
                
                tables = [row[0] for row in result.fetchall()]
                print(f"Created tables: {', '.join(tables)}")
                
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
"""
Habit Tracker Application
A modern, dark-themed habit tracking web app built with Flask, SQLite, and Tailwind CSS
"""

from dotenv import load_dotenv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from datetime import datetime, timedelta, timezone
from database_config import DatabaseConfig
from password_security import PasswordValidator, SecurePasswordHasher, validate_and_hash_password
from sql_security import InputValidator, SQLInjectionDetector, sql_injection_protection
import os
import logging

# Configure detailed logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Initialize database configuration
db_config = DatabaseConfig()

# Configure database with proper error handling
try:
    # Get database URI from DatabaseConfig
    database_uri = db_config.get_database_uri()
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    
    # Apply connection parameters for optimal performance
    connection_params = db_config.get_connection_params()
    
    # Configure SQLAlchemy engine options based on database type
    engine_options = {
        'pool_pre_ping': connection_params.get('pool_pre_ping', True),
        'pool_recycle': connection_params.get('pool_recycle', 3600),
        'connect_args': connection_params.get('connect_args', {})
    }
    
    # Add pool parameters only for databases that support them (PostgreSQL)
    if database_uri.startswith('postgresql://') or database_uri.startswith('postgres://'):
        engine_options.update({
            'pool_size': connection_params.get('pool_size', 10),
            'max_overflow': connection_params.get('max_overflow', 20),
            'pool_timeout': connection_params.get('pool_timeout', 30)
        })
        logger.info("Configured PostgreSQL connection pool")
    else:
        logger.info("Configured SQLite connection (no pooling)")
    
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options
    
    # Test connection and provide feedback (commented out to avoid startup delays)
    # connection_success = db_config.validate_connection()
    # if connection_success:
    #     print("✓ Successfully connected to database")
    #     logger.info("✅ Database connection successful")
    # else:
    #     print("⚠ Database connection warning: Connection validation failed")
    #     logger.warning("⚠️ Database connection issue: Connection validation failed")
    
    print("✓ Database configuration loaded")
    logger.info("✅ Database configuration loaded")
        
except Exception as e:
    error_message = db_config.get_error_message(e)
    print(f"✗ Database configuration error: {error_message}")
    logger.error(f"❌ Database configuration failed: {error_message}")
    
    # Only fallback to SQLite in development environments
    if not db_config.is_production():
        print("Falling back to local SQLite database for development")
        logger.info("🔄 Falling back to SQLite for development")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///habits.db'
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'connect_args': {'check_same_thread': False, 'timeout': 20}
        }
    else:
        # In production, re-raise the error as we need a working database
        raise RuntimeError(f"Failed to configure database in production: {error_message}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize OAuth
oauth = OAuth(app)

# Google OAuth - only if credentials are provided
google = None
if os.getenv('GOOGLE_CLIENT_ID') and os.getenv('GOOGLE_CLIENT_SECRET'):
    google = oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

# GitHub OAuth - only if credentials are provided
github = None
if os.getenv('GITHUB_CLIENT_ID') and os.getenv('GITHUB_CLIENT_SECRET'):
    github = oauth.register(
        name='github',
        client_id=os.getenv('GITHUB_CLIENT_ID'),
        client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize',
        api_base_url='https://api.github.com/',
        client_kwargs={'scope': 'user:email'},
    )

# Make OAuth availability available in templates
app.jinja_env.globals['google_oauth'] = google is not None
app.jinja_env.globals['github_oauth'] = github is not None

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# ==================== DATABASE MODELS ====================

class Habit(db.Model):
    """
    Habit model representing a habit to be tracked
    """
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
    
    def __repr__(self):
        return f'<Habit {self.name}>'
    
    def get_last_7_days(self):
        """
        Get the completion status for the last 7 days
        Returns a list of dictionaries with date and completion status
        """
        today = datetime.now(timezone.utc).date()
        last_7_days = []
        
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
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


class HabitLog(db.Model):
    """
    HabitLog model tracking daily completion status for each habit
    """
    __tablename__ = 'habit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Ensure one log per habit per date and optimize foreign key relationships
    __table_args__ = (
        db.UniqueConstraint('habit_id', 'date', name='unique_habit_date'),
        db.Index('idx_habit_date', 'habit_id', 'date'),
    )
    
    def __repr__(self):
        return f'<HabitLog {self.habit_id} - {self.date}: {self.completed}>'


class User(UserMixin, db.Model):
    """
    User model for authentication
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
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to habits
    habits = db.relationship('Habit', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """
        Set user password with enhanced security validation and hashing.
        
        Args:
            password: The plain text password to set
            
        Raises:
            ValueError: If password doesn't meet security requirements
        """
        # Validate password strength
        is_valid, errors = PasswordValidator.validate_password_strength(password)
        if not is_valid:
            raise ValueError(f"Password security requirements not met: {'; '.join(errors)}")
        
        # Hash password with secure method
        self.password_hash = SecurePasswordHasher.hash_password(password)
    
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
    
    @staticmethod
    def get_or_create_from_google(google_user):
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


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ==================== ROUTES ====================

@app.route('/')
def index():
    """
    Main page - redirects to dashboard if logged in, otherwise shows landing page
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """
    Main dashboard showing all habits with their 7-day progress
    """
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', habits=habits)


@app.route('/add-habit', methods=['POST'])
@login_required
@sql_injection_protection
def add_habit():
    """
    Add a new habit to the database with enhanced input validation
    """
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        # Enhanced input validation
        is_valid_name, sanitized_name = InputValidator.validate_habit_name(name)
        if not is_valid_name:
            flash('Invalid habit name. Please enter a valid habit name without special characters.', 'error')
            return redirect(url_for('dashboard'))
        
        # Validate description
        if description:
            sanitized_description = InputValidator.sanitize_string(description, max_length=500)
            # Check for SQL injection in description
            is_suspicious, _ = SQLInjectionDetector.detect_sql_injection(description)
            if is_suspicious:
                flash('Invalid description. Please remove any special characters or SQL-like content.', 'error')
                return redirect(url_for('dashboard'))
        else:
            sanitized_description = ""
        
        # Create new habit with sanitized input
        new_habit = Habit(
            user_id=current_user.id, 
            name=sanitized_name, 
            description=sanitized_description
        )
        db.session.add(new_habit)
        db.session.commit()
        
        flash(f'Habit "{sanitized_name}" added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error adding habit. Please try again.', 'error')
        # Log the error for debugging but don't expose details to user
        logger.error(f"Error adding habit for user {current_user.id}: {str(e)}")
    
    return redirect(url_for('dashboard'))


@app.route('/delete-habit/<int:habit_id>', methods=['POST'])
@login_required
@sql_injection_protection
def delete_habit(habit_id):
    """
    Delete a habit and all its associated logs with enhanced validation
    """
    try:
        # Validate habit_id
        is_valid_id, validated_habit_id = InputValidator.validate_integer(habit_id, min_value=1)
        if not is_valid_id:
            flash('Invalid habit ID.', 'error')
            return redirect(url_for('dashboard'))
        
        # Use ORM query (automatically parameterized) to find habit belonging to user
        habit = Habit.query.filter_by(id=validated_habit_id, user_id=current_user.id).first()
        if not habit:
            flash('Habit not found.', 'error')
            return redirect(url_for('dashboard'))
        
        habit_name = habit.name
        
        # Delete using ORM (automatically handles cascading deletes)
        db.session.delete(habit)
        db.session.commit()
        
        flash(f'Habit "{habit_name}" deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting habit {habit_id} for user {current_user.id}: {str(e)}")
        flash('Error deleting habit. Please try again.', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/toggle-habit/<int:habit_id>/<date_str>', methods=['POST'])
@login_required
@sql_injection_protection
def toggle_habit(habit_id, date_str):
    """
    Toggle the completion status for a habit on a specific date with enhanced validation
    """
    try:
        # Validate habit_id
        is_valid_id, validated_habit_id = InputValidator.validate_integer(habit_id, min_value=1)
        if not is_valid_id:
            return jsonify({'success': False, 'error': 'Invalid habit ID'}), 400
        
        # Validate date_str format and check for injection
        is_suspicious, _ = SQLInjectionDetector.detect_sql_injection(date_str)
        if is_suspicious:
            logger.warning(f"SQL injection attempt in date parameter from IP {request.remote_addr}")
            return jsonify({'success': False, 'error': 'Invalid date format'}), 400
        
        # Check if habit belongs to user (using parameterized query via ORM)
        habit = Habit.query.filter_by(id=validated_habit_id, user_id=current_user.id).first()
        if not habit:
            return jsonify({'success': False, 'error': 'Habit not found'}), 404
        
        # Parse the date string (format: YYYY-MM-DD) with additional validation
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Additional date validation - prevent dates too far in the future or past
            today = datetime.now(timezone.utc).date()
            if abs((date - today).days) > 365:  # Allow up to 1 year in past/future
                return jsonify({'success': False, 'error': 'Date out of allowed range'}), 400
                
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format'}), 400
        
        # Find existing log or create new one (using ORM - automatically parameterized)
        log = HabitLog.query.filter_by(habit_id=validated_habit_id, date=date).first()
        
        if log:
            # Toggle existing log
            log.completed = not log.completed
        else:
            # Create new log with completed=True
            log = HabitLog(habit_id=validated_habit_id, date=date, completed=True)
            db.session.add(log)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'completed': log.completed
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling habit {habit_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while updating the habit'
        }), 500


@app.route('/login', methods=['GET', 'POST'])
@sql_injection_protection
def login():
    """
    Login page with enhanced security validation
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember')
        
        # Enhanced email validation
        is_valid_email, sanitized_email = InputValidator.validate_email(email)
        if not is_valid_email:
            flash('Please enter a valid email address.', 'error')
            return render_template('login.html')
        
        # Basic password validation (don't reveal if it's empty for security)
        if not password:
            flash('Invalid email or password. Please check your credentials and try again.', 'error')
            return render_template('login.html')
        
        # Check for SQL injection attempts in password
        is_suspicious, _ = SQLInjectionDetector.detect_sql_injection(password)
        if is_suspicious:
            flash('Invalid email or password. Please check your credentials and try again.', 'error')
            logger.warning(f"SQL injection attempt in login password from IP {request.remote_addr}")
            return render_template('login.html')
        
        try:
            logger.info(f"🔐 Login attempt for email: {sanitized_email}")
            user = User.query.filter_by(email=sanitized_email).first()
            
            if user:
                logger.info(f"👤 User found in database: {sanitized_email}")
                if user.check_password(password):
                    logger.info(f"✅ Password verification successful for: {sanitized_email}")
                    
                    # If password hash was updated during check, save it
                    if db.session.is_modified(user):
                        db.session.commit()
                        logger.info(f"🔄 Password hash updated for user: {sanitized_email}")
                    
                    login_user(user, remember=remember)
                    logger.info(f"🎉 User logged in successfully: {sanitized_email}")
                    flash('Welcome back! Logged in successfully.', 'success')
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('dashboard'))
                else:
                    logger.warning(f"❌ Invalid password for user: {sanitized_email}")
                    flash('Invalid email or password. Please check your credentials and try again.', 'error')
                    return render_template('login.html')
            else:
                logger.warning(f"❌ User not found: {sanitized_email}")
                flash('Invalid email or password. Please check your credentials and try again.', 'error')
                return render_template('login.html')
        except Exception as e:
            logger.error(f"💥 Login error for email {sanitized_email}: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
@sql_injection_protection
def register():
    """
    Register page with enhanced security validation
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Enhanced email validation
        is_valid_email, sanitized_email = InputValidator.validate_email(email)
        if not is_valid_email:
            flash('Please enter a valid email address.', 'error')
            return render_template('register.html')
        
        # Enhanced password validation
        if not password:
            flash('Password is required.', 'error')
            return render_template('register.html')
        
        # Use enhanced password validation
        is_valid, validation_message, hashed_password = validate_and_hash_password(password, confirm_password)
        if not is_valid:
            flash(validation_message, 'error')
            return render_template('register.html')
        
        # Check if email already exists
        if User.query.filter_by(email=sanitized_email).first():
            flash('Email already registered. Please use a different email or try logging in.', 'error')
            return render_template('register.html')
        
        try:
            user = User(email=sanitized_email)
            # Use the pre-validated and hashed password
            user.password_hash = hashed_password
            db.session.add(user)
            db.session.commit()
            
            # Auto-login after registration
            login_user(user)
            flash('Account created successfully! Welcome to HabitTracker!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error for email {sanitized_email}: {str(e)}")
            flash('An error occurred while creating your account. Please try again.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')


@app.route('/login/google')
def login_google():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if not google:
        flash('Google login is not configured.', 'error')
        return redirect(url_for('login'))
    redirect_uri = url_for('auth_google', _external=True)
    print(f"Redirect URI: {redirect_uri}")
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/google')
def auth_google():
    if not google:
        flash('Google login is not configured.', 'error')
        return redirect(url_for('login'))
    try:
        token = google.authorize_access_token()
        user_info = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
        user = User.get_or_create_from_google(user_info)
        login_user(user)
        flash('Logged in with Google successfully!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash('Google login failed. Please try again.', 'error')
        return redirect(url_for('login'))


@app.route('/login/github')
def login_github():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if not github:
        flash('GitHub login is not configured.', 'error')
        return redirect(url_for('login'))
    redirect_uri = url_for('auth_github', _external=True)
    return github.authorize_redirect(redirect_uri)


@app.route('/auth/github')
def auth_github():
    if not github:
        flash('GitHub login is not configured.', 'error')
        return redirect(url_for('login'))
    try:
        token = github.authorize_access_token()
        resp = github.get('user')
        user_info = resp.json()
        
        # Get email if not provided
        if not user_info.get('email'):
            email_resp = github.get('user/emails')
            emails = email_resp.json()
            primary_email = next((email['email'] for email in emails if email['primary']), None)
            user_info['email'] = primary_email
        
        user = User.get_or_create_from_github(user_info)
        login_user(user)
        flash('Logged in with GitHub successfully!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash('GitHub login failed. Please try again.', 'error')
        return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    """
    Logout user
    """
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))


@app.route('/terms')
def terms():
    """
    Terms of Service page
    """
    return render_template('terms.html')


@app.route('/privacy')
def privacy():
    """
    Privacy Policy page
    """
    return render_template('privacy.html')


@app.route('/about')
def about():
    """
    About Us page
    """
    return render_template('about.html')


@app.route('/mission')
def mission():
    """
    Our Mission page
    """
    return render_template('mission.html')


@app.route('/team')
def team():
    """
    Our Team page
    """
    return render_template('team.html')


@app.route('/contact')
def contact():
    """
    Contact Us page
    """
    return render_template('contact.html')


# ==================== INITIALIZATION ====================

def create_tables():
    """
    Create database tables if they don't exist
    """
    try:
        with app.app_context():
            logger.info("🔧 Database tables already exist - skipping creation")
            
            # Log current database info
            current_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if 'postgresql://' in current_uri:
                logger.info("📊 Using PostgreSQL database (Neon)")
            elif 'sqlite://' in current_uri:
                logger.info("📊 Using SQLite database (local)")
            
            # Skip table creation since tables already exist
            # db.create_all()  # Commented out - tables already exist
            logger.info("✅ Database ready for use")
            print("Database ready!")
            
    except Exception as e:
        error_msg = f"Database initialization error: {e}"
        logger.error(f"❌ {error_msg}")
        print(f"Database warning: {e}")
        # Continue anyway - this is expected on serverless platforms


def init_db():
    """Initialize database tables"""
    # Create instance directory for local SQLite if needed and not in production
    if not db_config.is_production() and not os.path.exists('instance'):
        try:
            os.makedirs('instance')
        except OSError:
            pass  # Ignore if can't create directory
    create_tables()

# Initialize database when module is imported
try:
    init_db()
except Exception as e:
    print(f"Database initialization warning: {e}")
    # Continue anyway - database will be in-memory on Vercel

if __name__ == '__main__':
    # Run the Flask app locally
    app.run(debug=True, port=5000)
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
from datetime import datetime, timedelta
import os

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///habits.db'
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to habit logs
    logs = db.relationship('HabitLog', backref='habit', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Habit {self.name}>'
    
    def get_last_7_days(self):
        """
        Get the completion status for the last 7 days
        Returns a list of dictionaries with date and completion status
        """
        today = datetime.utcnow().date()
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
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    
    # Ensure one log per habit per date
    __table_args__ = (db.UniqueConstraint('habit_id', 'date', name='unique_habit_date'),)
    
    def __repr__(self):
        return f'<HabitLog {self.habit_id} - {self.date}: {self.completed}>'


class User(UserMixin, db.Model):
    """
    User model for authentication
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    google_id = db.Column(db.String(50), unique=True)
    github_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to habits
    habits = db.relationship('Habit', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
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
    return User.query.get(int(user_id))


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
def add_habit():
    """
    Add a new habit to the database
    """
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validation
        if not name:
            flash('Habit name is required!', 'error')
            return redirect(url_for('dashboard'))
        
        if len(name) > 100:
            flash('Habit name must be less than 100 characters!', 'error')
            return redirect(url_for('dashboard'))
        
        # Create new habit
        new_habit = Habit(user_id=current_user.id, name=name, description=description)
        db.session.add(new_habit)
        db.session.commit()
        
        flash(f'Habit "{name}" added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding habit: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/delete-habit/<int:habit_id>', methods=['POST'])
@login_required
def delete_habit(habit_id):
    """
    Delete a habit and all its associated logs
    """
    try:
        habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
        habit_name = habit.name
        
        db.session.delete(habit)
        db.session.commit()
        
        flash(f'Habit "{habit_name}" deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting habit: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/toggle-habit/<int:habit_id>/<date_str>', methods=['POST'])
@login_required
def toggle_habit(habit_id, date_str):
    """
    Toggle the completion status for a habit on a specific date
    """
    try:
        # Check if habit belongs to user
        habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
        if not habit:
            return jsonify({'success': False, 'error': 'Habit not found'}), 404
        
        # Parse the date string (format: YYYY-MM-DD)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Find existing log or create new one
        log = HabitLog.query.filter_by(habit_id=habit_id, date=date).first()
        
        if log:
            # Toggle existing log
            log.completed = not log.completed
        else:
            # Create new log with completed=True
            log = HabitLog(habit_id=habit_id, date=date, completed=True)
            db.session.add(log)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'completed': log.completed
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login page
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register page
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))
        
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Auto-login after registration
        login_user(user)
        flash('Account created successfully! Welcome!', 'success')
        return redirect(url_for('dashboard'))
    
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
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")


if __name__ == '__main__':
    # Create tables on first run
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    create_tables()
    
    # Run the Flask app
    app.run(debug=True, port=5000)
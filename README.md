# 🎯 HabitTracker

> **A modern, scalable habit tracking web application built with Flask, featuring layered architecture, comprehensive validation, and property-based testing.**

Track your daily habits with a beautiful interface, robust backend architecture, and enterprise-grade code quality that helps you build consistency and achieve your goals.

![Habit Tracker](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-2.0+-red)
![Architecture](https://img.shields.io/badge/Architecture-Layered-purple)
![Testing](https://img.shields.io/badge/Testing-Property--Based-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 🏗️ **Enterprise Architecture**
- **Layered Architecture**: Clean separation between controllers, services, and models
- **Factory Pattern**: Environment-based application configuration
- **Service Layer**: Business logic isolation with validation and authorization
- **Comprehensive Validation**: Input validation with descriptive error messages
- **CORS Support**: Configurable cross-origin resource sharing for modern frontends

### 🧪 **Advanced Testing**
- **Property-Based Testing**: 14 formal correctness properties using Hypothesis
- **Unit Testing**: Comprehensive test coverage for all components
- **Integration Testing**: Full workflow validation
- **Security Testing**: Protection against common vulnerabilities

### 📊 **Enhanced Habit Management**
- **Extended Model**: Execution time, frequency, habit types (useful/pleasant)
- **Business Rules**: Automatic validation of habit constraints
- **Related Habits**: Link habits together for complex workflows
- **Rewards System**: Configurable rewards for useful habits
- **RESTful API**: Standard HTTP endpoints with proper status codes

### 🎨 **Beautiful Modern Interface**
- **Dark Theme**: Professional slate/indigo color scheme with glass-morphism effects
- **Responsive Design**: Perfect experience on mobile, tablet, and desktop
- **Real-time Updates**: Smooth animations and instant feedback
- **7-Day Progress Tracking**: Visual completion status with progress indicators

### 🔐 **Security & Configuration**
- **Environment-Based Config**: Secure configuration management
- **OAuth Integration**: Google and GitHub social login
- **Input Sanitization**: Protection against XSS and SQL injection
- **Session Security**: Secure authentication with Flask-Login

## 🛠️ Technology Stack

### Backend Architecture
- **Flask** - Application factory pattern with blueprints
- **SQLAlchemy** - ORM with migration support
- **Service Layer** - Business logic with validation and authorization
- **Validators** - Reusable validation components
- **CORS** - Configurable cross-origin support

### Testing Framework
- **Hypothesis** - Property-based testing for correctness properties
- **pytest** - Unit and integration testing
- **Coverage** - Code coverage analysis (target: 90%+)

### Frontend
- **HTML5** - Semantic markup structure
- **Tailwind CSS** - Utility-first CSS framework
- **JavaScript** - Interactive functionality with API integration
- **RESTful API** - Standard HTTP endpoints

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

#### 1. Clone and Setup

```bash
git clone https://github.com/f1sherFM/Habit-Tracker.git
cd Habit-Tracker

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# Minimum required for development:
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

#### 3. Run Application

```bash
# Quick start (recommended)
python run.py

# Or run directly
python main.py

# Or use Flask CLI
flask run
```

The application will start on `http://localhost:5000`

### Environment Configuration

The application supports three environments with different configurations:

#### Development (Default)
```bash
FLASK_ENV=development
DATABASE_URL=sqlite:///dev.db  # Optional, defaults to SQLite
DEBUG=true  # Automatically set
```

#### Testing
```bash
FLASK_ENV=testing
# Uses in-memory SQLite database
# Disables CSRF protection for testing
```

#### Production
```bash
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key  # Required
DATABASE_URL=postgresql://...      # Required
CORS_ORIGINS=https://yourdomain.com  # Recommended
```

## 📁 Project Architecture

```
Habit-Tracker/
├── app/                          # Application package
│   ├── __init__.py              # Application factory
│   ├── config.py                # Environment-based configuration
│   ├── models/                  # Data models
│   │   ├── habit.py            # Enhanced habit model
│   │   ├── user.py             # User model
│   │   └── habit_types.py      # Habit type enums
│   ├── services/               # Business logic layer
│   │   ├── habit_service.py    # Habit management service
│   │   └── user_service.py     # User management service
│   ├── validators/             # Validation layer
│   │   ├── habit_validator.py  # Habit validation rules
│   │   ├── time_validator.py   # Time constraint validation
│   │   └── frequency_validator.py # Frequency validation
│   ├── api/                    # RESTful API endpoints
│   │   ├── habits.py          # Habit API routes
│   │   └── users.py           # User API routes
│   ├── utils/                  # Utility modules
│   │   └── cors_config.py     # CORS configuration
│   └── error_handlers.py       # Global error handling
├── tests/                      # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   ├── property/              # Property-based tests
│   └── security/              # Security tests
├── migrations/                 # Database migrations
├── templates/                  # HTML templates
├── main.py                    # Application entry point
├── run.py                     # Quick start script
├── .env.example              # Environment template
└── requirements.txt          # Dependencies
```

## 🧪 Testing

The application includes comprehensive testing with property-based testing for formal correctness verification.

### Run All Tests

```bash
# Run complete test suite
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test types
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/property/      # Property-based tests
pytest tests/security/      # Security tests
```

### Property-Based Testing

The application includes 14 formal correctness properties:

1. **Business Logic Delegation** - Controllers delegate to services
2. **Validator Usage** - Data validation through dedicated validators
3. **Habit Validation** - Complex habit constraint validation
4. **Error Messages** - Descriptive validation error messages
5. **Validation Format** - Standard validation result format
6. **Configuration Loading** - Environment variable configuration
7. **CORS Headers** - Proper CORS header handling
8. **Service Validation** - Pre-creation validation in services
9. **Authorization Checks** - User permission validation
10. **Cascade Deletion** - Related record cleanup
11. **Default Values** - Automatic default value assignment
12. **HTTP Status Codes** - Standard API response codes
13. **Data Migration** - Safe database migration
14. **Error Descriptions** - Specific error descriptions

### Test Coverage Goals

- **Minimum Coverage**: 90%
- **Critical Paths**: 100%
- **Property Tests**: All 14 properties covered
- **Security Tests**: All major vulnerabilities tested

## 🔧 API Documentation

### Habit Management API

#### Get Habits
```http
GET /api/habits
Authorization: Required (session-based)

Query Parameters:
- include_archived: boolean (default: false)
- type: string (useful|pleasant)
- page: integer (default: 1)
- per_page: integer (default: 20, max: 100)

Response: 200 OK
{
  "habits": [...],
  "total": 10,
  "page": 1,
  "per_page": 20
}
```

#### Create Habit
```http
POST /api/habits
Content-Type: application/json
Authorization: Required

Body:
{
  "name": "Morning Exercise",
  "description": "30 minutes of cardio",
  "execution_time": 1800,
  "frequency": 1,
  "habit_type": "useful",
  "reward": "Healthy breakfast"
}

Response: 201 Created
{
  "habit": {
    "id": 1,
    "name": "Morning Exercise",
    ...
  }
}
```

#### Update Habit
```http
PUT /api/habits/{id}
Content-Type: application/json
Authorization: Required

Response: 200 OK (updated habit)
```

#### Delete Habit
```http
DELETE /api/habits/{id}
Authorization: Required

Response: 204 No Content
```

### Error Responses

All API endpoints return standardized error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Habit data validation failed",
    "details": [
      {
        "field": "execution_time",
        "message": "Execution time cannot exceed 120 seconds"
      }
    ]
  },
  "timestamp": "2024-01-15T08:00:00Z",
  "path": "/api/habits"
}
```

## 🔒 Security Features

### Input Validation
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy ORM
- **XSS Prevention**: Input sanitization and output escaping
- **CSRF Protection**: Flask-WTF CSRF tokens
- **Input Length Limits**: Configurable maximum input lengths

### Authentication & Authorization
- **Session Management**: Secure session handling with Flask-Login
- **Password Security**: Bcrypt hashing with configurable rounds
- **OAuth Integration**: Google and GitHub social login
- **Permission Checks**: User-level authorization for all operations

### Configuration Security
- **Environment Variables**: Sensitive data in environment variables
- **Secret Key Validation**: Required secure secret keys in production
- **CORS Configuration**: Configurable allowed origins and methods
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection

## 🚀 Deployment

### Environment Setup

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Configure required variables**:
   ```bash
   # Required for production
   SECRET_KEY=your-secure-random-key
   DATABASE_URL=postgresql://user:pass@host:port/db
   FLASK_ENV=production
   
   # Optional but recommended
   CORS_ORIGINS=https://yourdomain.com
   ```

3. **Database migration**:
   ```bash
   # Run database migrations
   flask db upgrade
   ```

### Platform-Specific Deployment

#### Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

#### Heroku
```bash
# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DATABASE_URL=postgresql://...

# Deploy
git push heroku main
```

#### Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "main.py"]
```

## 🛠️ Development

### Adding New Features

1. **Models**: Add/modify models in `app/models/`
2. **Services**: Implement business logic in `app/services/`
3. **Validators**: Add validation rules in `app/validators/`
4. **API**: Create endpoints in `app/api/`
5. **Tests**: Add tests in appropriate `tests/` subdirectories

### Code Quality Standards

- **Type Hints**: Use type annotations for all functions
- **Docstrings**: Document all classes and methods
- **Error Handling**: Proper exception handling with custom exceptions
- **Logging**: Structured logging for debugging and monitoring
- **Testing**: Write tests for all new functionality

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Rollback migration
flask db downgrade
```

## 📊 Monitoring and Logging

### Application Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Application started")
logger.error("Error occurred", exc_info=True)
```

### Performance Monitoring
- **Request Logging**: Optional request/response logging
- **Error Tracking**: Structured error logging
- **Database Queries**: SQLAlchemy query logging in debug mode

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests (unit + property-based)
- Update documentation for new features
- Ensure 90%+ test coverage
- Add type hints for all functions

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Developer

**Main Developer**: Darklord  
**Contact**: [@f1sherFM](https://t.me/f1sherFM) (Telegram)

## 🆘 Support

For issues and questions:

1. **Check Documentation**: Review this README and related docs
2. **Run Tests**: Ensure your environment is set up correctly
3. **Check Logs**: Review application logs for error details
4. **Environment**: Verify environment variables are set correctly
5. **Dependencies**: Ensure all requirements are installed

### Common Issues

**Import Errors**
```bash
# Ensure you're in the virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Database Issues**
```bash
# Reset database (development only)
rm -f *.db
python main.py
```

**Configuration Issues**
```bash
# Verify environment variables
python -c "from app.config import get_config; print(get_config('development'))"
```

---

**Happy Habit Tracking with Enterprise-Grade Architecture!** 🎯
# Design Document: Database Persistence Fix

## Overview

This design addresses the critical database persistence issue on Vercel deployment by migrating from in-memory SQLite to PostgreSQL on Supabase. The current implementation loses all user data after each request due to the ephemeral nature of in-memory databases in serverless environments.

The solution implements a robust database abstraction layer that automatically selects the appropriate database based on the deployment environment, with comprehensive migration tools and connection management.

## Architecture

### Current Architecture Problems
- **In-Memory Database**: `sqlite:///:memory:` on Vercel loses data after each request
- **No Persistence**: User registrations and habits disappear immediately
- **Environment Coupling**: Hard-coded database selection based on VERCEL environment variable

### New Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Flask App     │───▶│  Database Layer  │───▶│   PostgreSQL    │
│                 │    │                  │    │   (Supabase)    │
│ - Routes        │    │ - Connection Mgr │    │                 │
│ - Models        │    │ - Migration Tool │    │ - Persistent    │
│ - Authentication│    │ - Error Handling │    │ - Encrypted     │
└─────────────────┘    └──────────────────┘    │ - Backed up     │
                                               └─────────────────┘
```

## Components and Interfaces

### Database Configuration Manager
**Purpose**: Manages database connections across different environments

**Interface**:
```python
class DatabaseConfig:
    def get_database_uri(self) -> str
    def is_production(self) -> bool
    def validate_connection(self) -> bool
    def get_connection_params(self) -> dict
```

**Implementation**:
- Reads environment variables for database credentials
- Automatically detects deployment environment
- Provides fallback configurations for development

### Migration Service
**Purpose**: Handles data migration from SQLite to PostgreSQL

**Interface**:
```python
class MigrationService:
    def migrate_users(self, source_db: str, target_db: str) -> bool
    def migrate_habits(self, source_db: str, target_db: str) -> bool
    def verify_migration(self, source_db: str, target_db: str) -> bool
    def rollback_migration(self, backup_path: str) -> bool
```
### Connection Pool Manager
**Purpose**: Manages database connections efficiently for concurrent requests

**Interface**:
```python
class ConnectionPoolManager:
    def get_connection(self) -> Connection
    def release_connection(self, conn: Connection) -> None
    def health_check(self) -> bool
    def configure_pool(self, max_connections: int, timeout: int) -> None
```

## Data Models

### Enhanced User Model
```python
class User(UserMixin, db.Model):
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
```

### Enhanced Habit Model
```python
class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_archived = db.Column(db.Boolean, default=False)
```

### Enhanced HabitLog Model
```python
class HabitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        db.UniqueConstraint('habit_id', 'date', name='unique_habit_date'),
        db.Index('idx_habit_date', 'habit_id', 'date'),
    )
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: User Registration Persistence
*For any* user registration with valid credentials, storing the user in the database and then querying for that user should return the same user data
**Validates: Requirements 1.1**

### Property 2: User Login Data Retrieval
*For any* registered user, attempting to login with correct credentials should successfully retrieve and authenticate the user from persistent storage
**Validates: Requirements 1.2**

### Property 3: Habit Data Persistence
*For any* habit created by a user, storing the habit and then querying for it should return the same habit data with all properties intact
**Validates: Requirements 1.3**

### Property 4: Environment-Based Database Selection
*For any* environment configuration, the system should automatically select the appropriate database URI based on environment variables
**Validates: Requirements 2.5**

### Property 5: Database Connection Error Handling
*For any* invalid database credentials or connection parameters, the system should provide clear, user-friendly error messages without exposing sensitive information
**Validates: Requirements 2.4**

### Property 6: Migration Data Preservation
*For any* existing user data, running the migration process should preserve all user accounts, habits, and habit logs without data loss
**Validates: Requirements 3.1, 3.2**

### Property 7: Migration Data Integrity Verification
*For any* completed migration, the data counts and essential relationships in the target database should match the source database
**Validates: Requirements 3.3**

### Property 8: Password Security
*For any* user password, the stored password hash should never match the plain text password and should use secure hashing algorithms
**Validates: Requirements 5.1**

### Property 9: SQL Injection Prevention
*For any* database query executed through the ORM, the query should use parameterized statements and not allow direct SQL injection
**Validates: Requirements 5.3**

## Error Handling

### Database Connection Failures
- **Connection Timeout**: Implement 30-second timeout for initial connections
- **Retry Logic**: Automatic retry with exponential backoff (1s, 2s, 4s, 8s)
- **Fallback Behavior**: Graceful degradation with user-friendly error messages
- **Health Checks**: Regular connection health monitoring

### Migration Error Handling
- **Pre-migration Validation**: Verify source database integrity before migration
- **Atomic Operations**: Use database transactions for migration steps
- **Progress Tracking**: Log migration progress for debugging
- **Rollback Capability**: Maintain backup for rollback if migration fails

### Runtime Error Management
- **Connection Pool Exhaustion**: Queue requests with timeout
- **Query Timeouts**: 15-second timeout for individual queries
- **Data Validation**: Comprehensive input validation before database operations
- **Logging**: Structured logging for all database operations and errors

## Testing Strategy

### Unit Testing
- **Database Configuration**: Test environment-based database URI selection
- **Model Validation**: Test data model constraints and relationships
- **Migration Logic**: Test individual migration functions with test data
- **Error Handling**: Test error scenarios with invalid inputs

### Property-Based Testing
- **User Registration Round-trip**: Test user creation and retrieval with random valid data
- **Habit Persistence**: Test habit creation and retrieval across multiple sessions
- **Migration Integrity**: Test migration with randomly generated datasets
- **Password Security**: Test password hashing with various input patterns

**Configuration**: Each property test runs minimum 100 iterations using pytest-hypothesis
**Tagging**: Each test tagged with format: **Feature: database-persistence-fix, Property {number}: {property_text}**

### Integration Testing
- **End-to-End User Flow**: Test complete user registration, login, and habit creation flow
- **Database Connection**: Test actual connections to Supabase in staging environment
- **Migration Testing**: Test migration with production-like data volumes
- **Performance Testing**: Test connection pooling under concurrent load
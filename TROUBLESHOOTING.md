# Troubleshooting Guide

This guide covers common issues and solutions for the Habit Tracker application deployment and operation.

## Database Issues

### 1. Database Connection Failures

#### Symptoms
```
Error: Database connection failed
Error: Database connection timed out
Error: Unable to connect to the database server
```

#### Diagnosis Steps
1. **Check DATABASE_URL format**:
   ```python
   import os
   print("DATABASE_URL:", os.getenv('DATABASE_URL', 'Not set'))
   ```

2. **Test connection manually**:
   ```python
   from database_config import DatabaseConfig
   db_config = DatabaseConfig()
   success, message = db_config.test_connection_with_feedback()
   print(f"Connection test: {success} - {message}")
   ```

3. **Check environment info**:
   ```python
   info = db_config.get_environment_info()
   for key, value in info.items():
       print(f"{key}: {value}")
   ```

#### Common Solutions

**Invalid DATABASE_URL Format**:
```bash
# Wrong
DATABASE_URL=postgres://user:pass@host:port/db

# Correct
DATABASE_URL=postgresql://user:pass@host:port/db
```

**Missing Environment Variable**:
- Verify DATABASE_URL is set in your deployment platform
- Check variable name spelling (case-sensitive)
- Ensure variable is available in the correct environment

**Network/Firewall Issues**:
- Verify Supabase project is running (green status in dashboard)
- Check if your deployment platform can reach external databases
- Test connection from a different network

**SSL Connection Issues**:
```bash
# Add SSL mode if needed
DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require
```

### 2. Data Not Persisting

#### Symptoms
- User registrations disappear after page refresh
- Habits are lost between sessions
- Application seems to work but data doesn't save

#### Diagnosis Steps
1. **Check if using in-memory database**:
   ```python
   from database_config import DatabaseConfig
   db_config = DatabaseConfig()
   uri = db_config.get_database_uri()
   print(f"Database URI: {uri}")
   
   if ':memory:' in uri:
       print("WARNING: Using in-memory database - data will not persist!")
   ```

2. **Verify database type**:
   ```python
   info = db_config.get_environment_info()
   print(f"Database type: {info['database_type']}")
   print(f"URI source: {info['database_uri_source']}")
   ```

#### Solutions

**In-Memory Database Issue**:
- Set DATABASE_URL environment variable
- Verify it's available in your deployment environment
- Restart your application after setting the variable

**Database Tables Not Created**:
```python
# Run database initialization
from app import app, db
with app.app_context():
    db.create_all()
    print("Database tables created")
```

### 3. Migration Issues

#### Symptoms
```
Error: Migration failed
Error: Data integrity verification failed
Error: Source database not found
```

#### Diagnosis Steps
1. **Check source database**:
   ```bash
   ls -la habits.db  # Check if SQLite file exists
   ```

2. **Verify target database connection**:
   ```python
   from migration_service import MigrationService
   migration = MigrationService()
   # Test will be in migration logs
   ```

#### Solutions

**Source Database Missing**:
- Ensure SQLite file exists before migration
- Check file permissions
- Verify file path is correct

**Target Database Connection Issues**:
- Follow database connection troubleshooting above
- Ensure target database is empty or prepared for migration

**Data Integrity Issues**:
- Check migration logs for specific errors
- Verify source data is valid
- Run migration in test environment first

## Authentication Issues

### 1. OAuth Login Failures

#### Google OAuth Issues

**Symptoms**:
```
Error: redirect_uri_mismatch
Error: invalid_client
Error: access_denied
```

**Solutions**:

1. **Redirect URI Mismatch**:
   - Check Google Cloud Console OAuth settings
   - Verify redirect URI matches exactly:
     ```
     Local: http://localhost:5000/auth/google/callback
     Production: https://your-domain.com/auth/google/callback
     ```
   - Ensure no trailing slashes or extra characters

2. **Invalid Client**:
   - Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are correct
   - Check environment variables are set in deployment platform
   - Ensure OAuth app is enabled in Google Cloud Console

3. **Domain Verification**:
   - Add your domain to authorized domains in Google Cloud Console
   - Verify domain ownership if required

#### GitHub OAuth Issues

**Symptoms**:
```
Error: Application suspended
Error: redirect_uri_mismatch
Error: bad_verification_code
```

**Solutions**:

1. **Redirect URI Issues**:
   - Check GitHub OAuth app settings
   - Verify callback URL: `https://your-domain.com/auth/github/callback`
   - Ensure URL is exactly as configured

2. **Application Configuration**:
   - Verify GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET
   - Check OAuth app is active (not suspended)
   - Ensure app has correct permissions

### 2. Session Management Issues

#### Symptoms
- Users logged out unexpectedly
- Session data not persisting
- "Please log in" errors for authenticated users

#### Solutions

1. **SECRET_KEY Issues**:
   ```python
   import os
   secret_key = os.getenv('SECRET_KEY')
   if not secret_key or len(secret_key) < 32:
       print("WARNING: SECRET_KEY is missing or too short")
   ```

2. **Session Configuration**:
   - Ensure SECRET_KEY is set and consistent across deployments
   - Use strong, random SECRET_KEY (64+ characters)
   - Don't change SECRET_KEY in production (invalidates all sessions)

## Deployment Issues

### 1. Vercel Deployment Failures

#### Build Failures

**Symptoms**:
```
Error: Build failed
Error: Module not found
Error: Python version not supported
```

**Solutions**:

1. **Python Version**:
   - Check `runtime.txt` specifies supported Python version
   - Verify version is supported by Vercel
   ```
   python-3.11.0
   ```

2. **Dependencies**:
   - Ensure all dependencies are in `requirements.txt`
   - Pin versions for reproducible builds
   - Check for conflicting dependencies

3. **Build Configuration**:
   - Verify `vercel.json` configuration is correct
   - Check build and route settings
   - Ensure API endpoint is properly configured

#### Runtime Failures

**Symptoms**:
```
Error: Function timeout
Error: Memory limit exceeded
Error: Internal server error
```

**Solutions**:

1. **Function Timeout**:
   - Increase timeout in `vercel.json`:
   ```json
   "functions": {
     "api/index.py": {
       "maxDuration": 30
     }
   }
   ```

2. **Memory Issues**:
   - Optimize database connection pooling
   - Reduce concurrent connections
   - Check for memory leaks in application code

3. **Cold Start Issues**:
   - Implement connection pooling
   - Use keep-alive for database connections
   - Consider warming functions

### 2. Environment Variable Issues

#### Symptoms
```
Error: Environment variable not found
Error: Configuration missing
Warning: Using fallback configuration
```

#### Diagnosis
```bash
# Check Vercel environment variables
vercel env ls

# Test variable access in function
vercel logs --follow
```

#### Solutions

1. **Missing Variables**:
   - Add all required environment variables in Vercel dashboard
   - Ensure variables are set for correct environment (Production/Preview)
   - Check variable names are exactly correct (case-sensitive)

2. **Variable Access Issues**:
   - Verify variables are available at runtime
   - Check if variables need to be prefixed (platform-specific)
   - Test variable loading in application startup

## Performance Issues

### 1. Slow Database Queries

#### Symptoms
- Page load times > 5 seconds
- Database timeout errors
- High response times

#### Diagnosis
```python
# Enable SQLAlchemy query logging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

#### Solutions

1. **Connection Pooling**:
   ```bash
   # Optimize pool settings
   DB_POOL_SIZE=15
   DB_MAX_OVERFLOW=25
   DB_POOL_TIMEOUT=30
   ```

2. **Query Optimization**:
   - Add database indexes for frequently queried fields
   - Use eager loading for relationships
   - Implement query caching where appropriate

3. **Database Performance**:
   - Monitor Supabase dashboard for slow queries
   - Consider upgrading database plan if needed
   - Optimize database schema

### 2. High Memory Usage

#### Symptoms
```
Error: Memory limit exceeded
Warning: High memory usage detected
```

#### Solutions

1. **Connection Pool Optimization**:
   - Reduce pool size if memory constrained
   - Implement connection recycling
   - Monitor connection usage

2. **Application Optimization**:
   - Implement pagination for large datasets
   - Use streaming for large responses
   - Optimize data structures

## Security Issues

### 1. SSL/TLS Connection Issues

#### Symptoms
```
Error: SSL connection failed
Warning: Insecure connection detected
Error: Certificate verification failed
```

#### Solutions

1. **Force SSL Connections**:
   ```bash
   DB_SSL_MODE=require
   ```

2. **Certificate Issues**:
   - Verify Supabase SSL certificates are valid
   - Check system certificate store is updated
   - Use proper SSL configuration

### 2. SQL Injection Warnings

#### Symptoms
```
Warning: Potential SQL injection detected
Error: Query validation failed
```

#### Solutions

1. **Use ORM Properly**:
   - Always use SQLAlchemy ORM methods
   - Never concatenate user input into SQL strings
   - Use parameterized queries

2. **Input Validation**:
   - Validate all user inputs
   - Use proper data types
   - Implement input sanitization

## Monitoring and Debugging

### 1. Enable Detailed Logging

```python
import logging

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable database query logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### 2. Health Check Endpoints

Add health check functionality:
```python
@app.route('/health')
def health_check():
    db_config = DatabaseConfig()
    db_success, db_message = db_config.test_connection_with_feedback()
    
    return jsonify({
        'status': 'healthy' if db_success else 'unhealthy',
        'database': db_message,
        'timestamp': datetime.utcnow().isoformat()
    })
```

### 3. Debug Information

```python
@app.route('/debug/info')
def debug_info():
    if not app.debug:
        return "Debug info only available in debug mode", 403
    
    db_config = DatabaseConfig()
    info = db_config.get_environment_info()
    
    return jsonify({
        'environment': info,
        'database_uri_type': 'PostgreSQL' if info['database_type'] == 'PostgreSQL' else 'SQLite',
        'is_production': info['is_production']
    })
```

## Getting Help

### 1. Collect Debug Information

Before seeking help, collect:
- Error messages (full stack traces)
- Environment information
- Database connection status
- Application logs
- Platform-specific logs (Vercel, Heroku, etc.)

### 2. Check Resources

1. **Application Logs**:
   ```bash
   # Vercel
   vercel logs
   
   # Heroku
   heroku logs --tail
   ```

2. **Database Status**:
   - Check Supabase dashboard
   - Monitor connection counts
   - Review query performance

3. **Platform Status**:
   - Check Vercel status page
   - Monitor platform-specific issues
   - Review platform documentation

### 3. Common Debug Commands

```bash
# Test database connection
python -c "from database_config import DatabaseConfig; print(DatabaseConfig().test_connection_with_feedback())"

# Check environment variables (be careful with secrets)
python -c "import os; print('DATABASE_URL set:', bool(os.getenv('DATABASE_URL')))"

# Validate SSL connection
python -c "from database_config import DatabaseConfig; print(DatabaseConfig().verify_ssl_connection())"

# Test migration (dry run)
python migrate.py --dry-run

# Check application health
curl https://your-app.com/health
```

This troubleshooting guide should help you diagnose and resolve most common issues. For persistent problems, check the application logs and platform-specific documentation.
# Environment Variables Configuration Guide

This guide covers all environment variables needed for the Habit Tracker application across different deployment environments.

## Overview

The application uses environment variables for:
- Database configuration
- OAuth authentication
- Security settings
- Performance tuning

## Required Environment Variables

### Database Configuration

#### DATABASE_URL (Required)
```bash
DATABASE_URL=postgresql://postgres:[password]@[host]:[port]/[database]
```

**Description**: Primary database connection string
**Example**: `postgresql://postgres:mypassword@db.abc123.supabase.co:5432/postgres`
**Environment**: All (Production, Preview, Development)

**Format Guidelines**:
- Use `postgresql://` or `postgres://` prefix
- Include username (usually `postgres` for Supabase)
- Include password (URL-encoded if contains special characters)
- Include host (your Supabase project host)
- Include port (usually `5432` for PostgreSQL)
- Include database name (usually `postgres` for Supabase)

### OAuth Configuration

#### Google OAuth (Required for Google login)
```bash
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

**Setup Instructions**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - Local: `http://localhost:5000/auth/google/callback`
   - Production: `https://your-domain.com/auth/google/callback`

#### GitHub OAuth (Required for GitHub login)
```bash
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
```

**Setup Instructions**:
1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in application details:
   - Application name: "Habit Tracker"
   - Homepage URL: Your app URL
   - Authorization callback URL: `https://your-domain.com/auth/github/callback`
4. Copy Client ID and Client Secret

### Security Configuration

#### SECRET_KEY (Required)
```bash
SECRET_KEY=your-secure-secret-key-for-production
```

**Description**: Flask session encryption key
**Requirements**: 
- Minimum 32 characters
- Use cryptographically secure random string
- Different for each environment

**Generate Secure Key**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Optional Environment Variables

### Database Performance Tuning

#### DB_POOL_SIZE
```bash
DB_POOL_SIZE=10
```
**Description**: Number of database connections in pool
**Default**: 10
**Recommended**: 5-20 depending on expected load

#### DB_MAX_OVERFLOW
```bash
DB_MAX_OVERFLOW=20
```
**Description**: Additional connections beyond pool size
**Default**: 20
**Recommended**: 10-30 depending on traffic spikes

#### DB_POOL_TIMEOUT
```bash
DB_POOL_TIMEOUT=30
```
**Description**: Timeout in seconds for getting connection from pool
**Default**: 30
**Recommended**: 15-60 depending on application needs

### Database Security

#### DB_SSL_MODE
```bash
DB_SSL_MODE=require
```
**Description**: SSL connection requirement
**Default**: require
**Options**: disable, allow, prefer, require, verify-ca, verify-full

#### DB_SSL_CERT, DB_SSL_KEY, DB_SSL_ROOT_CERT
```bash
DB_SSL_CERT=/path/to/client-cert.pem
DB_SSL_KEY=/path/to/client-key.pem
DB_SSL_ROOT_CERT=/path/to/ca-cert.pem
```
**Description**: SSL certificate files (usually not needed for Supabase)
**Default**: None (Supabase handles SSL automatically)

## Environment-Specific Configuration

### Development (.env file)
```bash
# Database - Local SQLite fallback
# DATABASE_URL not set = uses sqlite:///habits.db

# OAuth - Development apps
GOOGLE_CLIENT_ID=dev_google_client_id
GOOGLE_CLIENT_SECRET=dev_google_secret
GITHUB_CLIENT_ID=dev_github_client_id
GITHUB_CLIENT_SECRET=dev_github_secret

# Security - Development key
SECRET_KEY=development-secret-key-not-for-production

# Performance - Lower limits for development
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

### Production (Vercel/Cloud)
```bash
# Database - Supabase PostgreSQL
DATABASE_URL=postgresql://postgres:prod_password@db.prod123.supabase.co:5432/postgres

# OAuth - Production apps
GOOGLE_CLIENT_ID=prod_google_client_id
GOOGLE_CLIENT_SECRET=prod_google_secret
GITHUB_CLIENT_ID=prod_github_client_id
GITHUB_CLIENT_SECRET=prod_github_secret

# Security - Strong production key
SECRET_KEY=super-secure-64-character-random-string-for-production-use

# Performance - Production optimized
DB_POOL_SIZE=15
DB_MAX_OVERFLOW=25
DB_POOL_TIMEOUT=30
DB_SSL_MODE=require
```

## Setting Environment Variables

### Local Development

1. **Create .env file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file**:
   ```bash
   nano .env  # or your preferred editor
   ```

3. **Add your values**:
   - Replace placeholder values with actual credentials
   - Never commit .env to version control

### Vercel Deployment

1. **Via Vercel Dashboard**:
   - Go to project Settings → Environment Variables
   - Add each variable individually
   - Select appropriate environments (Production, Preview, Development)

2. **Via Vercel CLI**:
   ```bash
   # Add variables interactively
   vercel env add DATABASE_URL
   vercel env add GOOGLE_CLIENT_ID
   vercel env add GOOGLE_CLIENT_SECRET
   vercel env add GITHUB_CLIENT_ID
   vercel env add GITHUB_CLIENT_SECRET
   vercel env add SECRET_KEY
   
   # List all variables
   vercel env ls
   
   # Remove a variable
   vercel env rm VARIABLE_NAME
   ```

3. **Bulk Import** (from .env file):
   ```bash
   # Note: Be careful with this approach in production
   vercel env pull .env.vercel
   ```

### Other Cloud Platforms

#### Heroku
```bash
heroku config:set DATABASE_URL="postgresql://..."
heroku config:set GOOGLE_CLIENT_ID="your_id"
heroku config:set SECRET_KEY="your_key"
```

#### Railway
```bash
railway variables set DATABASE_URL="postgresql://..."
railway variables set GOOGLE_CLIENT_ID="your_id"
```

## Validation and Testing

### Environment Variable Validation

The application includes built-in validation:

1. **Database Connection Test**:
   ```python
   from database_config import DatabaseConfig
   db_config = DatabaseConfig()
   success, message = db_config.test_connection_with_feedback()
   print(f"Database: {message}")
   ```

2. **Environment Info**:
   ```python
   info = db_config.get_environment_info()
   print(f"Environment: {info}")
   ```

### Common Validation Errors

1. **Missing DATABASE_URL**:
   ```
   Warning: Running on Vercel without DATABASE_URL - using in-memory SQLite
   ```
   **Solution**: Set DATABASE_URL environment variable

2. **Invalid Database Format**:
   ```
   Error: Database connection failed
   ```
   **Solution**: Check DATABASE_URL format and credentials

3. **OAuth Configuration Issues**:
   ```
   Error: OAuth client not configured
   ```
   **Solution**: Verify GOOGLE_CLIENT_ID/SECRET and GITHUB_CLIENT_ID/SECRET

## Security Best Practices

### Environment Variable Security

1. **Never Commit Secrets**:
   - Add .env to .gitignore
   - Use .env.example for templates
   - Never include actual credentials in code

2. **Use Strong Values**:
   - Generate cryptographically secure SECRET_KEY
   - Use strong database passwords
   - Rotate secrets regularly

3. **Principle of Least Privilege**:
   - Use separate OAuth apps for dev/prod
   - Limit database user permissions
   - Use read-only credentials where possible

### Production Security Checklist

- [ ] DATABASE_URL uses strong password
- [ ] SECRET_KEY is cryptographically secure (64+ characters)
- [ ] OAuth apps configured with correct redirect URIs
- [ ] SSL connections enforced (DB_SSL_MODE=require)
- [ ] Environment variables not exposed in logs
- [ ] Separate credentials for each environment

## Troubleshooting

### Common Issues

1. **Environment Variables Not Loading**:
   ```python
   import os
   print("DATABASE_URL:", os.getenv('DATABASE_URL'))
   ```

2. **Database Connection Issues**:
   - Check DATABASE_URL format
   - Verify database is running
   - Test connection manually

3. **OAuth Redirect Errors**:
   - Verify redirect URIs match exactly
   - Check domain configuration
   - Ensure HTTPS in production

### Debug Commands

```bash
# Check environment variables (be careful not to expose secrets)
env | grep -E "(DATABASE|GOOGLE|GITHUB|SECRET)"

# Test database connection
python -c "from database_config import DatabaseConfig; print(DatabaseConfig().test_connection_with_feedback())"

# Validate environment
python -c "from database_config import DatabaseConfig; print(DatabaseConfig().get_environment_info())"
```

## Support

For environment configuration issues:
1. Check application logs for specific error messages
2. Verify all required variables are set
3. Test each component individually
4. Consult platform-specific documentation (Vercel, Heroku, etc.)
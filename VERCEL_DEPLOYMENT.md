# Vercel Deployment Guide

This guide covers deploying the Habit Tracker application to Vercel with PostgreSQL database support.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Supabase Database**: Set up PostgreSQL database following [SUPABASE_SETUP.md](./SUPABASE_SETUP.md)
3. **OAuth Applications**: Configure Google and GitHub OAuth apps

## Environment Variables Setup

### Required Environment Variables

Add these environment variables in your Vercel project settings:

#### Database Configuration
```
DATABASE_URL=postgresql://postgres:[password]@[host]:[port]/[database]
```
- Replace with your actual Supabase PostgreSQL connection string
- Example: `postgresql://postgres:your_password@db.your_project_ref.supabase.co:5432/postgres`

#### OAuth Credentials
```
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
```

#### Application Security
```
SECRET_KEY=your-secure-secret-key-for-production
```
- Generate a strong, random secret key for production
- Use a tool like `python -c "import secrets; print(secrets.token_hex(32))"`

#### Optional Database Settings
```
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_SSL_MODE=require
```

### Setting Environment Variables in Vercel

1. **Via Vercel Dashboard**:
   - Go to your project settings
   - Navigate to "Environment Variables"
   - Add each variable with appropriate environment (Production, Preview, Development)

2. **Via Vercel CLI**:
   ```bash
   vercel env add DATABASE_URL
   vercel env add GOOGLE_CLIENT_ID
   vercel env add GOOGLE_CLIENT_SECRET
   vercel env add GITHUB_CLIENT_ID
   vercel env add GITHUB_CLIENT_SECRET
   vercel env add SECRET_KEY
   ```

## Deployment Steps

### 1. Initial Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from project root
vercel

# Follow the prompts:
# - Link to existing project or create new
# - Set up project settings
# - Deploy
```

### 2. Configure Environment Variables

After initial deployment, add all required environment variables through the Vercel dashboard or CLI.

### 3. Database Migration

If migrating from existing SQLite data:

```bash
# Run migration locally first (recommended)
python migrate.py

# Or run migration after deployment using Vercel Functions
# (Note: This requires the migration script to be accessible via API endpoint)
```

### 4. Verify Deployment

1. **Check Database Connection**:
   - Visit your deployed app
   - Try registering a new user
   - Verify data persists after page refresh

2. **Test OAuth Integration**:
   - Test Google OAuth login
   - Test GitHub OAuth login
   - Ensure redirect URLs are configured correctly

## Vercel Configuration Details

### vercel.json Configuration

The `vercel.json` file includes:

- **Environment Variable References**: Uses Vercel's secret management
- **Function Timeout**: Set to 30 seconds for database operations
- **Build Configuration**: Optimized for Python Flask application

### Function Limits

- **Execution Time**: 30 seconds (configurable up to 60s on Pro plan)
- **Memory**: 1024MB default (configurable on Pro plan)
- **Concurrent Executions**: 1000 (varies by plan)

## Troubleshooting

### Common Issues

1. **Database Connection Timeout**:
   ```
   Error: Database connection timed out
   ```
   - **Solution**: Check DATABASE_URL format and network connectivity
   - **Verify**: Supabase database is running and accessible

2. **Environment Variables Not Found**:
   ```
   Error: Missing required environment variable
   ```
   - **Solution**: Verify all environment variables are set in Vercel dashboard
   - **Check**: Variable names match exactly (case-sensitive)

3. **OAuth Redirect Errors**:
   ```
   Error: redirect_uri_mismatch
   ```
   - **Solution**: Update OAuth app redirect URLs to match Vercel domain
   - **Format**: `https://your-app.vercel.app/auth/google/callback`

4. **SSL Connection Issues**:
   ```
   Error: SSL connection failed
   ```
   - **Solution**: Ensure `DB_SSL_MODE=require` is set
   - **Verify**: Supabase SSL certificates are valid

### Debug Steps

1. **Check Vercel Function Logs**:
   ```bash
   vercel logs
   ```

2. **Test Database Connection**:
   - Use the database configuration test endpoint (if implemented)
   - Check Supabase dashboard for connection attempts

3. **Verify Environment Variables**:
   ```bash
   vercel env ls
   ```

## Performance Optimization

### Database Connection Pooling

The application automatically configures connection pooling for PostgreSQL:

- **Pool Size**: 10 connections (configurable via `DB_POOL_SIZE`)
- **Max Overflow**: 20 additional connections (configurable via `DB_MAX_OVERFLOW`)
- **Pool Timeout**: 30 seconds (configurable via `DB_POOL_TIMEOUT`)

### Caching Considerations

- **Static Assets**: Automatically cached by Vercel CDN
- **Database Queries**: Consider implementing query caching for frequently accessed data
- **Session Management**: Uses secure server-side sessions

## Security Best Practices

1. **Environment Variables**:
   - Never commit secrets to version control
   - Use Vercel's secret management system
   - Rotate secrets regularly

2. **Database Security**:
   - Always use SSL connections (`DB_SSL_MODE=require`)
   - Use strong database passwords
   - Limit database user permissions

3. **Application Security**:
   - Use strong SECRET_KEY for session management
   - Keep dependencies updated
   - Monitor for security vulnerabilities

## Monitoring and Maintenance

### Health Checks

The application includes built-in health checks:
- Database connection validation
- SSL connection verification
- Environment configuration validation

### Monitoring

1. **Vercel Analytics**: Monitor function performance and errors
2. **Supabase Dashboard**: Monitor database performance and connections
3. **Application Logs**: Use `vercel logs` for debugging

### Maintenance Tasks

1. **Regular Updates**:
   - Update Python dependencies
   - Monitor Vercel platform updates
   - Update OAuth application settings as needed

2. **Database Maintenance**:
   - Monitor connection pool usage
   - Optimize slow queries
   - Regular database backups (handled by Supabase)

## Support

For deployment issues:
1. Check Vercel documentation: [vercel.com/docs](https://vercel.com/docs)
2. Review Supabase documentation: [supabase.com/docs](https://supabase.com/docs)
3. Check application logs for specific error messages
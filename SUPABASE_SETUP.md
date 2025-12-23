# Supabase PostgreSQL Setup Guide

This guide will help you set up Supabase PostgreSQL for the Habit Tracker application.

## Step 1: Create Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Click "Start your project" and sign up with GitHub, Google, or email
3. Verify your email if required

## Step 2: Create New Project

1. Click "New Project" in your dashboard
2. Choose your organization (or create a new one)
3. Fill in project details:
   - **Name**: `habit-tracker-db` (or your preferred name)
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose closest to your users (e.g., US East, Europe West)
4. Click "Create new project"
5. Wait 1-2 minutes for project initialization

## Step 3: Get Database Connection Details

1. Once your project is ready, go to **Settings** → **Database**
2. In the "Connection info" section, you'll see:
   - **Host**: `db.your_project_ref.supabase.co`
   - **Database name**: `postgres`
   - **Port**: `5432`
   - **User**: `postgres`
   - **Password**: The password you set during project creation

## Step 4: Get Connection String

1. In the Database settings, scroll to "Connection string"
2. Select "URI" tab
3. Copy the connection string that looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.your_project_ref.supabase.co:5432/postgres
   ```

## Step 5: Update Environment Variables

1. Open your `.env` file
2. Replace the `DATABASE_URL` value with your actual Supabase connection string:
   ```
   DATABASE_URL=postgresql://postgres:your_actual_password@db.your_project_ref.supabase.co:5432/postgres
   ```

## Step 6: Configure Vercel Environment Variables (for deployment)

1. Go to your Vercel dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Add the following variables:
   - **Name**: `DATABASE_URL`
   - **Value**: Your Supabase connection string
   - **Environment**: Production, Preview, Development (select all)

## Security Notes

- Never commit your actual `.env` file to version control
- Use strong passwords for your database
- The connection uses SSL by default (secure)
- Supabase provides automatic backups and security updates

## Troubleshooting

### Connection Issues
- Verify your password is correct
- Check that your project is fully initialized (green status in Supabase dashboard)
- Ensure your connection string format is correct

### SSL Errors
- Supabase requires SSL connections by default
- If you get SSL errors, ensure your PostgreSQL client supports SSL

### Firewall Issues
- Supabase is accessible from anywhere by default
- No firewall configuration needed for most deployments

## Next Steps

After completing this setup:
1. The application will automatically use PostgreSQL instead of SQLite
2. Your data will persist across deployments
3. You can view and manage your data in the Supabase dashboard

For more help, visit the [Supabase Documentation](https://supabase.com/docs).
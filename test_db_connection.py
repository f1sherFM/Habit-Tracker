#!/usr/bin/env python3
"""
Test database connection script
Tests the current DATABASE_URL configuration
"""

import sys
import os
from database_config import DatabaseConfig

def test_connection():
    """Test the database connection and provide detailed feedback."""
    print("🔍 Testing database connection...")
    print("-" * 50)
    
    # Initialize database config
    db_config = DatabaseConfig()
    
    # Get environment info
    env_info = db_config.get_environment_info()
    print(f"Environment: {'Production' if env_info['is_production'] else 'Development'}")
    print(f"Database Type: {env_info['database_type']}")
    print(f"URI Source: {env_info['database_uri_source']}")
    print(f"Connection Pooling: {env_info['connection_pooling']}")
    print()
    
    # Test connection
    success, message = db_config.test_connection_with_feedback()
    
    if success:
        print("✅ " + message)
        print("\n🎉 Database connection successful!")
        return True
    else:
        print("❌ " + message)
        print("\n💡 Troubleshooting suggestions:")
        print("1. Check your internet connection")
        print("2. Verify the DATABASE_URL in your .env file")
        print("3. Ensure your Supabase project is active")
        print("4. Try accessing your Supabase dashboard to confirm the project exists")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
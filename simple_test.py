#!/usr/bin/env python3
"""
Simple database connection test
"""

from dotenv import load_dotenv
import os
from database_config import DatabaseConfig

# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

print("🔍 Simple database test...")
print("-" * 30)

db_config = DatabaseConfig()
database_uri = db_config.get_database_uri()

print(f"Database URI: {database_uri[:50]}...")
print(f"Is Production: {db_config.is_production()}")

# Simple connection test
if db_config.validate_connection():
    print("✅ Connection successful!")
else:
    print("❌ Connection failed!")

print("-" * 30)
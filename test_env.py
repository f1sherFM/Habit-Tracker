#!/usr/bin/env python3
"""
Test environment variables loading
"""

from dotenv import load_dotenv
import os

# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

print("🔍 Testing environment variables...")
print("-" * 50)

database_url = os.getenv('DATABASE_URL')
print(f"DATABASE_URL: {database_url}")

if database_url:
    if 'neon.tech' in database_url:
        print("✅ Neon database URL detected")
    elif 'supabase.co' in database_url:
        print("❌ Old Supabase URL still detected!")
    else:
        print("⚠️ Unknown database URL format")
else:
    print("❌ DATABASE_URL not found")

print("-" * 50)
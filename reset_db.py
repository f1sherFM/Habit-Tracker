#!/usr/bin/env python3
"""
Reset database connections and test table creation
"""

from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
import logging

# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_connections():
    """Reset database connections"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        print("🔄 Creating new engine...")
        engine = create_engine(database_url, pool_pre_ping=True)
        
        print("🔍 Testing simple query...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✅ Query result: {result.fetchone()}")
        
        print("🔍 Checking existing tables...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Existing tables: {tables}")
        
        engine.dispose()
        print("✅ Connection test successful")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    reset_connections()
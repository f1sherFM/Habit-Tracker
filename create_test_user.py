#!/usr/bin/env python3
"""
Create a test user in the new Neon database
"""

from dotenv import load_dotenv
import os
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text
import logging

# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_user():
    """Create a test user in the database"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        print("🔄 Connecting to database...")
        engine = create_engine(database_url, pool_pre_ping=True)
        
        # User details - CHANGE THESE TO YOUR ACTUAL DETAILS
        email = "kirillka229top@gmail.com"  # Your actual email
        password = "BFAf!sheR09"   # Your actual password  
        name = "Kirill"                     # Your actual name
        
        # Hash the password
        password_hash = generate_password_hash(password)
        
        print(f"👤 Creating user: {email}")
        
        with engine.connect() as conn:
            # Check if user already exists
            result = conn.execute(text("""
                SELECT id FROM users WHERE email = :email
            """), {"email": email})
            
            existing_user = result.fetchone()
            
            if existing_user:
                print(f"✅ User already exists with ID: {existing_user[0]}")
                return True
            
            # Create new user
            result = conn.execute(text("""
                INSERT INTO users (email, password_hash, name, created_at, updated_at, is_active)
                VALUES (:email, :password_hash, :name, NOW(), NOW(), true)
                RETURNING id
            """), {
                "email": email,
                "password_hash": password_hash,
                "name": name
            })
            
            user_id = result.fetchone()[0]
            conn.commit()
            
            print(f"✅ User created successfully with ID: {user_id}")
            print(f"📧 Email: {email}")
            print(f"🔑 Password: {password}")
            print("\n🎉 You can now login with these credentials!")
            
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating test user in Neon database...")
    print("=" * 50)
    
    success = create_test_user()
    
    if success:
        print("\n✅ Test user creation completed!")
        print("Now try logging in to your Vercel app with the credentials above.")
    else:
        print("\n❌ Failed to create test user.")
        print("Check your DATABASE_URL and try again.")
#!/usr/bin/env python3
"""
Habit Tracker - Quick Start Script
Run this script to start the Habit Tracker application
"""

import sys
import subprocess
import os

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def install_requirements():
    """Install required packages"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Error installing dependencies!")
        sys.exit(1)

def run_application():
    """Run the Flask application"""
    print("\n🚀 Starting Habit Tracker application...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server\n")
    
    try:
        # Import and run the app
        import app
        app.create_tables()
        app.app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Application stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

def main():
    """Main function"""
    print("=" * 50)
    print("    HABIT TRACKER - Setup & Launch")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Ask if user wants to install requirements
    print("\n📦 Checking dependencies...")
    response = input("Do you want to install/update dependencies? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        install_requirements()
    
    # Run the application
    run_application()

if __name__ == "__main__":
    main()
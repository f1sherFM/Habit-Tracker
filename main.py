"""
Habit Tracker Application - Main Entry Point

This is the main application file that uses the factory pattern
to create and configure the Flask application.
"""
import os
from app import create_app

# Determine configuration based on environment
config_name = os.environ.get('FLASK_ENV', 'development')

# Create application using factory pattern
app = create_app(config_name)

if __name__ == '__main__':
    # Run the application
    debug_mode = config_name == 'development'
    port = int(os.environ.get('PORT', 5000))
    
    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=port
    )
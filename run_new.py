"""
New Flask Application Entry Point

Uses the new application factory pattern with environment-based configuration
"""
import os
from app import create_app
from app.validators.config_validator import ConfigValidator

def main():
    """Main application entry point"""
    
    # Validate configuration before starting
    validation_result = ConfigValidator.validate_all()
    if not validation_result.is_valid:
        print("❌ Configuration validation failed:")
        for error in validation_result.errors:
            print(f"  - {error}")
        return
    
    print("✅ Configuration validation passed")
    
    # Get environment
    env = os.environ.get('FLASK_ENV', 'development')
    print(f"🚀 Starting application in {env} mode")
    
    # Create Flask app
    app = create_app(env)
    
    # Run the application
    if env == 'development':
        app.run(debug=True, port=5000)
    else:
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

if __name__ == '__main__':
    main()
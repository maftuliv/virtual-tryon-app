"""
Main Flask application entry point.

Uses application factory pattern for clean dependency injection.
"""

from backend.app_factory import create_app_from_env

# Create application instance
app = create_app_from_env()

if __name__ == "__main__":
    import os

    # Get configuration
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    print("=" * 60)
    print("Virtual Try-On Server Starting...")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("=" * 60)

    # Run application
    app.run(host="0.0.0.0", port=port, debug=debug)

"""
Entry point for the application.

This module initializes and runs the Flask application.

Imports:
    from app: Imports the create_app function to create the Flask application instance.

Functions:
    create_app(): Creates and configures the Flask application instance.

Execution:
    If this module is run as the main program,
     it starts the Flask development server on host 0.0.0.0 and port 5000 with debug mode disabled.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

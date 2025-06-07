"""Routes initialization module.

This module sets up the main blueprint and API documentation for the application.
"""

from flask import Blueprint
from flask_restx import Api
from app.routes.chat import chat_namespace

# Import blueprints from other route modules
# from .onsite_management import onsite_bp

# Create a main blueprint to register all other blueprints
main_bp = Blueprint("main", __name__)

# Register blueprints
# main_bp.register_blueprint(onsite_bp, url_prefix="/onsite")
# Api object for swagger documentation
api = Api(
    title="GA API",
    version="1.0",
    description="API for GA system",
    doc="/docs/",
)

api.add_namespace(chat_namespace)
# Register the main blueprint with the API

api.init_app(main_bp)

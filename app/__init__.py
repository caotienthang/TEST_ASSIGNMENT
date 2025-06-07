"""Flask application factory module.

This module contains the application factory function and initializes Flask extensions.
"""

import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app.utils import is_production
from .config import Config
from app.core.Qdrant_chatbot import embedder


def create_app(config_class=Config):
    """Create and configure the Flask application.

    Args:
        config_class: Configuration class to use for the application.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(
        app,
        origins=[
            "http://127.0.0.1:3000",
            "http://localhost:3000",
            "*",
            "http://127.0.0.1:5500"
        ],
        supports_credentials=True
    )

    # Tạo collection
    embedder.create_collection("medical_dialogues")

    # Xử lý file dialogue
    print("Đang xử lý file dialogues...")
    embedder.process_dialogue_file('structured_chat_data.json')
    # Register Blueprints
    from .routes import main_bp

    app.register_blueprint(main_bp)

    return app

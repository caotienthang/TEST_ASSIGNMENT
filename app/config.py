"""Configuration module for the Flask application.

This module contains configuration classes for different environments (development, testing, production).
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "postgresql+psycopg2://postgres:postgres@0.0.0.0/cbhotel"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False



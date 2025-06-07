"""Utility functions module.

This module contains various utility functions used throughout the application.
"""


def is_production():
    """Check if the application is running in production environment.

    Returns:
        bool: True if the environment is set to production, False otherwise.
    """
    import os

    return os.environ.get("ENVIRONMENT") == "prod"

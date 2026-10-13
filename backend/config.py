"""Settings for the backend, read from environment variables.

For local development they come from the .env file in the project root (git-ignored;
see .env.example). On the hosting service they are set in its dashboard.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Config:
    # Used by Flask to sign data (and later the login tokens). Must be a long random
    # value in production.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    TESTING = False


class TestConfig(Config):
    TESTING = True
    # A throwaway SQLite database in memory: fast, needs no PostgreSQL.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

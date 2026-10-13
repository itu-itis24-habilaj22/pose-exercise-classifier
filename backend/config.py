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
    BCRYPT_ROUNDS = 12  # cost of hashing a password: higher = slower to crack
    TOKEN_DAYS = 7      # how long a login lasts
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # largest accepted request (a camera frame), bytes


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-only-secret-key-at-least-32-bytes"  # independent of .env
    BCRYPT_ROUNDS = 4  # fast hashing so the tests stay quick
    # A throwaway SQLite database in memory: fast, needs no PostgreSQL.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

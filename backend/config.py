"""Settings for the backend. Values can be overridden with environment variables."""
import os


class Config:
    # Used by Flask to sign data (and later the login tokens). Must be a long random
    # value in production, set via the SECRET_KEY environment variable.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    TESTING = False


class TestConfig(Config):
    TESTING = True

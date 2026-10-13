import sys
from pathlib import Path

# Let tests import modules from src/ the same way the scripts do.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


import pytest  # noqa: E402

from backend.app import create_app  # noqa: E402
from backend.config import TestConfig  # noqa: E402
from backend.db import db  # noqa: E402
from backend.seed import init_db  # noqa: E402


@pytest.fixture
def app():
    """Backend app with a fresh in-memory database (tables + exercises) for each test."""
    app = create_app(TestConfig)
    with app.app_context():
        init_db()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A fake browser that sends requests to the app without starting a server."""
    return app.test_client()

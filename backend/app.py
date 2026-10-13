"""Create and run the Flask app.

Run the development server (from the project root, with .venv activated):
    python -m backend.app
Then open http://127.0.0.1:5000/api/health in a browser.
"""
from flask import Flask

from backend.config import Config
from backend.routes import health


def create_app(config=Config):
    """Build the app. Tests pass TestConfig; the real server uses Config."""
    app = Flask(__name__)
    app.config.from_object(config)
    app.register_blueprint(health.bp)
    return app


if __name__ == "__main__":
    create_app().run(debug=True)

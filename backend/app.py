"""Create and run the Flask app.

Run the development server (from the project root, with .venv activated):
    python -m backend.app
Then open http://127.0.0.1:5000/api/health in a browser.

Create the database tables (once, and after adding new tables):
    flask --app backend.app init-db
"""
import click
from flask import Flask

from backend import models  # noqa: F401  (registers the tables with SQLAlchemy)
from backend.config import Config
from backend.db import db
from backend.routes import auth, exercises, health, history, workouts
from backend.seed import init_db


def create_app(config=Config):
    """Build the app. Tests pass TestConfig; the real server uses Config."""
    app = Flask(__name__)
    app.config.from_object(config)
    if not app.config["SQLALCHEMY_DATABASE_URI"]:
        raise RuntimeError("DATABASE_URL is not set: copy .env.example to .env and fill it in.")
    db.init_app(app)
    app.register_blueprint(health.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(exercises.bp)
    app.register_blueprint(workouts.bp)
    app.register_blueprint(history.bp)

    @app.cli.command("init-db")
    def init_db_command():
        """Create the tables and add the exercises."""
        added = init_db()
        click.echo(f"Tables ready. Exercises added: {added}.")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)

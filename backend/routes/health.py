"""GET /api/health: tells whether the server and the database are working. Used to test
the setup and, later, by the hosting service to check that the app is alive."""
from flask import Blueprint, jsonify
from sqlalchemy import text

from backend.db import db

bp = Blueprint("health", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        database = "ok"
    except Exception as error:  # report the problem instead of crashing
        database = f"error: {error.__class__.__name__}"
    status_code = 200 if database == "ok" else 503
    return jsonify(status="ok" if database == "ok" else "degraded", database=database), status_code

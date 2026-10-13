"""GET /api/health: tells whether the server is running. Used to test the setup and,
later, by the hosting service to check that the app is alive."""
from flask import Blueprint, jsonify

bp = Blueprint("health", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    return jsonify(status="ok")

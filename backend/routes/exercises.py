"""The supported exercises (public: the website shows them before login too).

GET /api/exercises -> 200 {"exercises": [...]}
"""
from flask import Blueprint, jsonify

from backend.db import db
from backend.models import Exercise

bp = Blueprint("exercises", __name__, url_prefix="/api/exercises")


@bp.get("")
def list_exercises():
    exercises = db.session.scalars(db.select(Exercise).order_by(Exercise.exercise_id))
    return jsonify(exercises=[e.to_dict() for e in exercises])

"""A user's workout plans (CRUD). Every endpoint needs the login token, and a user only
ever sees their own workouts.

GET    /api/workouts        -> 200 {"workouts": [...]}
POST   /api/workouts        {"name", "exercises": [{"exercise", "sets", "target_reps"}]} -> 201
GET    /api/workouts/<id>   -> 200 {"workout"}
PUT    /api/workouts/<id>   same body as POST -> 200 {"workout"}
DELETE /api/workouts/<id>   -> 204
"""
from flask import Blueprint, g, jsonify, request

from backend.auth import login_required
from backend.db import db
from backend.models import Exercise, Workout

bp = Blueprint("workouts", __name__, url_prefix="/api/workouts")

MAX_EXERCISES = 20
MAX_SETS = 20
MAX_REPS = 200


def is_whole_number(value, low, high):
    # bool is a subclass of int in Python, so exclude it explicitly
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def parse_workout(data):
    """Check a POST/PUT body; returns (name, exercises, error message or None)."""
    name = str(data.get("name", "")).strip()
    exercises = data.get("exercises")
    if not 1 <= len(name) <= 100:
        return None, None, "Name must be 1 to 100 characters."
    if not isinstance(exercises, list) or not 1 <= len(exercises) <= MAX_EXERCISES:
        return None, None, f"A workout needs 1 to {MAX_EXERCISES} exercises."

    known = set(db.session.scalars(db.select(Exercise.name)))
    cleaned = []
    for item in exercises:
        if not isinstance(item, dict) or item.get("exercise") not in known:
            return None, None, f"Each exercise must be one of: {', '.join(sorted(known))}."
        if not is_whole_number(item.get("sets"), 1, MAX_SETS):
            return None, None, f"Sets must be a whole number from 1 to {MAX_SETS}."
        if not is_whole_number(item.get("target_reps"), 1, MAX_REPS):
            return None, None, f"Target reps must be a whole number from 1 to {MAX_REPS}."
        cleaned.append({key: item[key] for key in ("exercise", "sets", "target_reps")})
    return name, cleaned, None


def own_workout(workout_id):
    """The current user's workout with this id, or None. Another user's workout also gives
    None, so the API doesn't even reveal that it exists."""
    workout = db.session.get(Workout, workout_id)
    return workout if workout is not None and workout.user_id == g.user.user_id else None


@bp.get("")
@login_required
def list_workouts():
    workouts = db.session.scalars(db.select(Workout).filter_by(user_id=g.user.user_id)
                                  .order_by(Workout.created_at))
    return jsonify(workouts=[w.to_dict() for w in workouts])


@bp.post("")
@login_required
def create_workout():
    name, exercises, error = parse_workout(request.get_json(silent=True) or {})
    if error:
        return jsonify(error=error), 400
    workout = Workout(user=g.user, name=name, exercises=exercises)
    db.session.add(workout)
    db.session.commit()
    return jsonify(workout=workout.to_dict()), 201


@bp.get("/<int:workout_id>")
@login_required
def get_workout(workout_id):
    workout = own_workout(workout_id)
    if workout is None:
        return jsonify(error="Workout not found."), 404
    return jsonify(workout=workout.to_dict())


@bp.put("/<int:workout_id>")
@login_required
def update_workout(workout_id):
    workout = own_workout(workout_id)
    if workout is None:
        return jsonify(error="Workout not found."), 404
    name, exercises, error = parse_workout(request.get_json(silent=True) or {})
    if error:
        return jsonify(error=error), 400
    workout.name, workout.exercises = name, exercises
    db.session.commit()
    return jsonify(workout=workout.to_dict())


@bp.delete("/<int:workout_id>")
@login_required
def delete_workout(workout_id):
    workout = own_workout(workout_id)
    if workout is None:
        return jsonify(error="Workout not found."), 404
    db.session.delete(workout)
    db.session.commit()
    return "", 204

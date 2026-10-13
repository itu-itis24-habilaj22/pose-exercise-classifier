"""Saved exercise results and the statistics computed from them.

POST /api/history   {"exercise", "reps_completed", "duration", "form_score"?, "voice_enabled"?}
                    -> 201 {"entry"}
GET  /api/history   ?exercise=squat&from=2026-11-01&to=2026-11-30  -> 200 {"history": [...]}
GET  /api/stats     -> 200 {"stats"}                       (everyone: basic stats)
GET  /api/progress  ?days=30 -> 200 {"progress"}            (premium: data for the charts)
"""
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, g, jsonify, request

from backend.auth import login_required, premium_required
from backend.db import db
from backend.models import Exercise, ExerciseHistory
from backend.validation import is_whole_number

bp = Blueprint("history", __name__, url_prefix="/api")

MAX_REPS = 1000
MAX_DURATION = 4 * 60 * 60  # seconds
MAX_PROGRESS_DAYS = 365


def as_utc(moment):
    """SQLite (used in tests) forgets the time zone; all our times are UTC."""
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def parse_entry(data):
    """Check a POST body; returns (fields for ExerciseHistory, error message or None)."""
    exercise = db.session.scalar(db.select(Exercise).filter_by(name=data.get("exercise")))
    if exercise is None:
        return None, "Unknown exercise."
    if not is_whole_number(data.get("reps_completed"), 0, MAX_REPS):
        return None, f"reps_completed must be a whole number from 0 to {MAX_REPS}."
    if not is_whole_number(data.get("duration"), 1, MAX_DURATION):
        return None, f"duration must be a whole number of seconds from 1 to {MAX_DURATION}."
    form_score = data.get("form_score")
    if form_score is not None and (isinstance(form_score, bool)
                                   or not isinstance(form_score, (int, float))
                                   or not 0 <= form_score <= 100):
        return None, "form_score must be a number from 0 to 100 (or left out)."
    voice_enabled = data.get("voice_enabled", False)
    if not isinstance(voice_enabled, bool):
        return None, "voice_enabled must be true or false."
    return {"exercise": exercise, "reps_completed": data["reps_completed"],
            "duration": data["duration"], "form_score": form_score,
            "voice_enabled": voice_enabled}, None


def parse_day(text):
    """'2026-11-03' -> date, or None if missing; raises ValueError if malformed."""
    return date.fromisoformat(text) if text else None


def my_history():
    """All of the current user's entries, oldest first."""
    return db.session.scalars(db.select(ExerciseHistory)
                              .filter_by(user_id=g.user.user_id)
                              .order_by(ExerciseHistory.date_completed)).all()


@bp.post("/history")
@login_required
def add_entry():
    fields, error = parse_entry(request.get_json(silent=True) or {})
    if error:
        return jsonify(error=error), 400
    entry = ExerciseHistory(user=g.user, **fields)
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry=entry.to_dict()), 201


@bp.get("/history")
@login_required
def list_history():
    try:
        first_day, last_day = parse_day(request.args.get("from")), parse_day(request.args.get("to"))
    except ValueError:
        return jsonify(error="Dates must look like 2026-11-30."), 400
    exercise = request.args.get("exercise")

    entries = []
    for entry in reversed(my_history()):  # newest first
        day = as_utc(entry.date_completed).date()
        if exercise and entry.exercise.name != exercise:
            continue
        if (first_day and day < first_day) or (last_day and day > last_day):
            continue
        entries.append(entry.to_dict())
    return jsonify(history=entries)


@bp.get("/stats")
@login_required
def stats():
    entries = my_history()
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    per_exercise = defaultdict(lambda: {"sessions": 0, "total_reps": 0, "best_set": 0})
    for entry in entries:
        item = per_exercise[entry.exercise.name]
        item["sessions"] += 1
        item["total_reps"] += entry.reps_completed
        item["best_set"] = max(item["best_set"], entry.reps_completed)
    scores = [e.form_score for e in entries if e.form_score is not None]
    return jsonify(stats={
        "total_sessions": len(entries),
        "total_reps": sum(e.reps_completed for e in entries),
        "total_duration": sum(e.duration for e in entries),
        "reps_this_week": sum(e.reps_completed for e in entries
                              if as_utc(e.date_completed) >= week_ago),
        "average_form_score": round(sum(scores) / len(scores), 1) if scores else None,
        "per_exercise": dict(per_exercise),
    })


@bp.get("/progress")
@premium_required
def progress():
    try:
        days = int(request.args.get("days", 30))
    except ValueError:
        days = 0
    if not 1 <= days <= MAX_PROGRESS_DAYS:
        return jsonify(error=f"days must be a whole number from 1 to {MAX_PROGRESS_DAYS}."), 400

    today = datetime.now(timezone.utc).date()
    first_day = today - timedelta(days=days - 1)
    exercises = list(db.session.scalars(db.select(Exercise.name).order_by(Exercise.exercise_id)))
    reps = {name: defaultdict(int) for name in exercises}
    for entry in my_history():
        day = as_utc(entry.date_completed).date()
        if day >= first_day:
            reps[entry.exercise.name][day] += entry.reps_completed

    all_days = [first_day + timedelta(days=i) for i in range(days)]
    return jsonify(progress={
        "days": [d.isoformat() for d in all_days],
        "reps": {name: [reps[name][d] for d in all_days] for name in exercises},
    })

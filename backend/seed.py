"""Create the tables and add the 3 supported exercises.

Run (from the project root, with .venv activated):
    flask --app backend.app init-db
Safe to run again: existing tables and exercises are left as they are.
"""
from backend.db import db
from backend.models import Exercise

EXERCISES = [
    {
        "name": "pushup",
        "display_name": "Push-up",
        "instructions": "Hands slightly wider than shoulders, body in a straight line from head "
                        "to heels. Lower your chest until your elbows are at about 90 degrees, "
                        "then push back up until your arms are straight.",
        "target_reps": 10,
        "difficulty": "intermediate",
        # Must match src/rep_counter.py EXERCISES.
        "joints_to_track": {"signal": "angle", "joint": "elbow"},
    },
    {
        "name": "squat",
        "display_name": "Squat",
        "instructions": "Feet shoulder-width apart, chest up. Push your hips back and bend your "
                        "knees until your thighs are about parallel to the floor, then stand "
                        "back up fully.",
        "target_reps": 10,
        "difficulty": "beginner",
        "joints_to_track": {"signal": "angle", "joint": "knee"},
    },
    {
        "name": "curl",
        "display_name": "Biceps Curl",
        "instructions": "Stand straight holding the weight with your arms down, elbows close to "
                        "your body. Bend your elbows to lift the weight to your shoulders, then "
                        "lower it slowly. Don't swing your back.",
        "target_reps": 10,
        "difficulty": "beginner",
        "joints_to_track": {"signal": "wrist_height", "joint": "elbow"},
    },
]


def init_db():
    """Create missing tables and add missing exercises; returns how many were added."""
    db.create_all()
    added = 0
    for data in EXERCISES:
        if db.session.execute(db.select(Exercise).filter_by(name=data["name"])).first() is None:
            db.session.add(Exercise(**data))
            added += 1
    db.session.commit()
    return added

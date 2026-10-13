from backend.db import db


class Exercise(db.Model):
    __tablename__ = "exercises"

    exercise_id = db.Column(db.Integer, primary_key=True)
    # Same names as the ML code (rep_counter.EXERCISES and the classifier): pushup, squat, curl.
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    demo_video_url = db.Column(db.String(500))  # demo videos come in Phase 4
    instructions = db.Column(db.Text, nullable=False)
    target_reps = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # beginner / intermediate / advanced
    # What the rep counter tracks, e.g. {"signal": "angle", "joint": "knee"}.
    joints_to_track = db.Column(db.JSON, nullable=False)

    def __repr__(self):
        return f"<Exercise {self.name}>"

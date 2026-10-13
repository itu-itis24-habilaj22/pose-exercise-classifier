from backend.db import db
from backend.models.user import utc_now


class Workout(db.Model):
    """A workout plan made by a user, e.g. "Monday Push Day"."""

    __tablename__ = "workouts"

    workout_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    # The plan, in order: [{"exercise": "pushup", "sets": 3, "target_reps": 10}, ...]
    exercises = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now,
                           onupdate=utc_now)

    user = db.relationship("User", back_populates="workouts")

    def to_dict(self):
        return {
            "workout_id": self.workout_id,
            "name": self.name,
            "exercises": self.exercises,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Workout {self.name}>"

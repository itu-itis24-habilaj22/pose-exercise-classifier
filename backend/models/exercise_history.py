from backend.db import db
from backend.models.user import utc_now


class ExerciseHistory(db.Model):
    """One finished exercise (one set) by a user: what the app saves after a session."""

    __tablename__ = "exercise_history"

    history_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercises.exercise_id"), nullable=False)
    reps_completed = db.Column(db.Integer, nullable=False)
    form_score = db.Column(db.Float)  # 0-100, average over the set; form feedback is Phase 4
    date_completed = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    duration = db.Column(db.Integer, nullable=False)  # seconds
    voice_enabled = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="history")
    exercise = db.relationship("Exercise")

    def to_dict(self):
        return {
            "history_id": self.history_id,
            "exercise": self.exercise.name,
            "reps_completed": self.reps_completed,
            "form_score": self.form_score,
            "date_completed": self.date_completed.isoformat(),
            "duration": self.duration,
            "voice_enabled": self.voice_enabled,
        }

    def __repr__(self):
        return f"<ExerciseHistory {self.user_id} {self.exercise_id} {self.reps_completed} reps>"

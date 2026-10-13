from datetime import datetime, timezone

from backend.db import db


def utc_now():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    # Never the password itself: a one-way hash of it (made with bcrypt, next step).
    password_hash = db.Column(db.String(255), nullable=False)
    subscription_tier = db.Column(db.String(20), nullable=False, default="free")  # free / premium
    stripe_customer_id = db.Column(db.String(255))  # set when the user first pays (Phase 4)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    workouts = db.relationship("Workout", back_populates="user", cascade="all, delete-orphan")
    history = db.relationship("ExerciseHistory", back_populates="user",
                              cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"

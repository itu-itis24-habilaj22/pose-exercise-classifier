"""Database tables. Importing this package registers all of them with SQLAlchemy."""
from backend.models.exercise import Exercise
from backend.models.exercise_history import ExerciseHistory
from backend.models.user import User
from backend.models.workout import Workout

__all__ = ["Exercise", "ExerciseHistory", "User", "Workout"]

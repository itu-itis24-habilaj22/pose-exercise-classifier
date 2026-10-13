import pytest
from sqlalchemy.exc import IntegrityError

from backend.db import db
from backend.models import Exercise, ExerciseHistory, User, Workout
from backend.seed import init_db


def make_user(name="faby"):
    user = User(username=name, email=f"{name}@example.com", password_hash="not-a-real-hash")
    db.session.add(user)
    db.session.commit()
    return user


def test_seed_adds_the_three_exercises(app):
    names = {e.name for e in db.session.scalars(db.select(Exercise))}
    assert names == {"pushup", "squat", "curl"}


def test_seed_twice_adds_nothing(app):
    assert init_db() == 0
    assert len(db.session.scalars(db.select(Exercise)).all()) == 3


def test_new_user_is_free_tier_with_timestamp(app):
    user = make_user()
    assert user.subscription_tier == "free"
    assert user.created_at is not None


def test_email_must_be_unique(app):
    make_user("faby")
    db.session.add(User(username="other", email="faby@example.com", password_hash="x"))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_workout_and_history_belong_to_user(app):
    user = make_user()
    squat = db.session.scalars(db.select(Exercise).filter_by(name="squat")).one()
    db.session.add(Workout(user=user, name="Leg day",
                           exercises=[{"exercise": "squat", "sets": 3, "target_reps": 10}]))
    db.session.add(ExerciseHistory(user=user, exercise=squat, reps_completed=12, duration=45))
    db.session.commit()

    assert user.workouts[0].exercises[0]["exercise"] == "squat"
    assert user.history[0].exercise.name == "squat"
    assert user.history[0].voice_enabled is False


def test_deleting_user_deletes_their_workouts_and_history(app):
    user = make_user()
    curl = db.session.scalars(db.select(Exercise).filter_by(name="curl")).one()
    db.session.add(Workout(user=user, name="Arms"))
    db.session.add(ExerciseHistory(user=user, exercise=curl, reps_completed=8, duration=30))
    db.session.commit()

    db.session.delete(user)
    db.session.commit()
    assert db.session.scalars(db.select(Workout)).all() == []
    assert db.session.scalars(db.select(ExerciseHistory)).all() == []

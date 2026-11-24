from datetime import datetime, timedelta, timezone

import pytest

from backend.db import db
from backend.models import ExerciseHistory, User


def signup(client, name="faby"):
    body = {"username": name, "email": f"{name}@example.com", "password": "password123"}
    token = client.post("/api/auth/signup", json=body).get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def faby(client):
    return signup(client)


def save(client, headers, exercise="squat", reps=10, duration=60, **extra):
    body = {"exercise": exercise, "reps_completed": reps, "duration": duration, **extra}
    return client.post("/api/history", json=body, headers=headers)


def backdate(days):
    """Move the most recent entry `days` into the past."""
    entry = db.session.scalars(db.select(ExerciseHistory)
                               .order_by(ExerciseHistory.history_id.desc())).first()
    entry.date_completed = datetime.now(timezone.utc) - timedelta(days=days)
    db.session.commit()


def make_premium():
    for user in db.session.scalars(db.select(User)):
        user.subscription_tier = "premium"
    db.session.commit()


def test_history_needs_login(client):
    assert client.get("/api/history").status_code == 401
    assert client.post("/api/history", json={}).status_code == 401
    assert client.get("/api/stats").status_code == 401


def test_save_and_list(client, faby):
    saved = save(client, faby, "pushup", reps=12, duration=40, form_score=87.5, voice_enabled=True)
    assert saved.status_code == 201
    entry = saved.get_json()["entry"]
    assert entry["exercise"] == "pushup" and entry["reps_completed"] == 12
    assert entry["form_score"] == 87.5 and entry["voice_enabled"] is True
    assert client.get("/api/history", headers=faby).get_json()["history"] == [entry]


GOOD = {"exercise": "squat", "reps_completed": 10, "duration": 60}


@pytest.mark.parametrize("change", [
    {"exercise": "burpee"},
    {"reps_completed": -1},
    {"reps_completed": "10"},
    {"duration": 0},
    {"form_score": 101},
    {"form_score": "good"},
    {"voice_enabled": "yes"},
])
def test_invalid_entries_are_rejected(client, faby, change):
    assert client.post("/api/history", json={**GOOD, **change}, headers=faby).status_code == 400


def test_history_filters(client, faby):
    save(client, faby, "squat")
    backdate(10)
    save(client, faby, "curl")
    history = client.get("/api/history", headers=faby).get_json()["history"]
    assert [h["exercise"] for h in history] == ["curl", "squat"]  # newest first

    only_squats = client.get("/api/history?exercise=squat", headers=faby).get_json()["history"]
    assert [h["exercise"] for h in only_squats] == ["squat"]
    since = (datetime.now(timezone.utc) - timedelta(days=3)).date().isoformat()
    recent = client.get(f"/api/history?from={since}", headers=faby).get_json()["history"]
    assert [h["exercise"] for h in recent] == ["curl"]
    assert client.get("/api/history?from=yesterday", headers=faby).status_code == 400


def test_stats(client, faby):
    save(client, faby, "squat", reps=10, duration=60, form_score=80)
    save(client, faby, "squat", reps=15, duration=70, form_score=90)
    save(client, faby, "pushup", reps=20, duration=50)
    backdate(10)  # the push-ups were 10 days ago

    stats = client.get("/api/stats", headers=faby).get_json()["stats"]
    assert stats["total_sessions"] == 3
    assert stats["total_reps"] == 45
    assert stats["total_duration"] == 180
    assert stats["reps_this_week"] == 25
    assert stats["average_form_score"] == 85.0  # entries without a score don't count
    assert stats["per_exercise"]["squat"] == {"sessions": 2, "total_reps": 25, "best_set": 15}


def test_stats_for_new_user(client, faby):
    stats = client.get("/api/stats", headers=faby).get_json()["stats"]
    assert stats["total_reps"] == 0 and stats["average_form_score"] is None


def test_progress_is_premium_only(client, faby):
    assert client.get("/api/progress", headers=faby).status_code == 403
    make_premium()
    assert client.get("/api/progress", headers=faby).status_code == 200


def test_progress_reps_per_day(client, faby):
    make_premium()
    save(client, faby, "squat", reps=10)
    save(client, faby, "squat", reps=5)
    save(client, faby, "curl", reps=8)
    backdate(2)
    save(client, faby, "pushup", reps=30)
    backdate(40)  # outside the 7-day window

    progress = client.get("/api/progress?days=7", headers=faby).get_json()["progress"]
    assert len(progress["days"]) == 7
    assert progress["reps"]["squat"][-1] == 15   # today
    assert progress["reps"]["curl"][-3] == 8     # 2 days ago
    assert sum(progress["reps"]["pushup"]) == 0
    assert client.get("/api/progress?days=0", headers=faby).status_code == 400


def test_users_only_see_their_own_history(client, faby):
    save(client, faby, "squat", reps=10)
    other = signup(client, "other")
    assert client.get("/api/history", headers=other).get_json()["history"] == []
    assert client.get("/api/stats", headers=other).get_json()["stats"]["total_reps"] == 0

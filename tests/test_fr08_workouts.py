import pytest

PLAN = {"name": "Monday Push Day",
        "exercises": [{"exercise": "pushup", "sets": 3, "target_reps": 10},
                      {"exercise": "curl", "sets": 2, "target_reps": 12}]}


def login_header(client, name):
    body = {"username": name, "email": f"{name}@example.com", "password": "password123"}
    token = client.post("/api/auth/signup", json=body).get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def faby(client):
    return login_header(client, "faby")


def create(client, headers, plan=PLAN):
    return client.post("/api/workouts", json=plan, headers=headers)


def test_exercises_list_is_public(client):
    response = client.get("/api/exercises")
    assert response.status_code == 200
    assert [e["name"] for e in response.get_json()["exercises"]] == ["pushup", "squat", "curl"]


def test_workouts_need_login(client):
    assert client.get("/api/workouts").status_code == 401
    assert client.post("/api/workouts", json=PLAN).status_code == 401


def test_create_list_get(client, faby):
    created = create(client, faby)
    assert created.status_code == 201
    workout = created.get_json()["workout"]
    assert workout["name"] == "Monday Push Day" and workout["exercises"] == PLAN["exercises"]

    listed = client.get("/api/workouts", headers=faby).get_json()["workouts"]
    assert [w["workout_id"] for w in listed] == [workout["workout_id"]]
    one = client.get(f"/api/workouts/{workout['workout_id']}", headers=faby)
    assert one.get_json()["workout"] == workout


def test_update_and_delete(client, faby):
    workout_id = create(client, faby).get_json()["workout"]["workout_id"]
    new_plan = {
        "name": "Leg day",
        "exercises": [{"exercise": "squat", "sets": 4, "target_reps": 8}],
    }
    updated = client.put(f"/api/workouts/{workout_id}", json=new_plan, headers=faby)
    assert updated.status_code == 200
    assert updated.get_json()["workout"]["name"] == "Leg day"

    assert client.delete(f"/api/workouts/{workout_id}", headers=faby).status_code == 204
    assert client.get(f"/api/workouts/{workout_id}", headers=faby).status_code == 404
    assert client.get("/api/workouts", headers=faby).get_json()["workouts"] == []


@pytest.mark.parametrize("bad_plan", [
    {"name": "", "exercises": PLAN["exercises"]},                                    # no name
    {"name": "Empty", "exercises": []},                                              # no exercises
    {"name": "X", "exercises": [{"exercise": "burpee", "sets": 3, "target_reps": 10}]},  # unknown
    {"name": "X", "exercises": [{"exercise": "squat", "sets": 0, "target_reps": 10}]},   # 0 sets
    {"name": "X", "exercises": [{"exercise": "squat", "sets": 3, "target_reps": "10"}]},  # text
    {"name": "X", "exercises": [{"exercise": "squat", "sets": True, "target_reps": 10}]},  # bool
])
def test_invalid_workouts_are_rejected(client, faby, bad_plan):
    assert create(client, faby, bad_plan).status_code == 400


def test_users_cannot_see_or_change_each_others_workouts(client, faby):
    workout_id = create(client, faby).get_json()["workout"]["workout_id"]
    other = login_header(client, "other")
    assert client.get("/api/workouts", headers=other).get_json()["workouts"] == []
    assert client.get(f"/api/workouts/{workout_id}", headers=other).status_code == 404
    assert client.put(f"/api/workouts/{workout_id}", json=PLAN, headers=other).status_code == 404
    assert client.delete(f"/api/workouts/{workout_id}", headers=other).status_code == 404
    assert client.get(f"/api/workouts/{workout_id}", headers=faby).status_code == 200  # untouched

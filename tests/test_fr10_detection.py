import io
from pathlib import Path

import cv2
import pytest

from backend.ml_engine import models_available

VIDEOS = Path(__file__).resolve().parent.parent / "data" / "raw_videos"

pytestmark = pytest.mark.skipif(not models_available(),
                                reason="needs the git-ignored model files in models/")


@pytest.fixture
def auth(client):
    body = {"username": "faby", "email": "faby@example.com", "password": "password123"}
    token = client.post("/api/auth/signup", json=body).get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


def start(client, auth, exercise=None):
    response = client.post("/api/detect/sessions", json={"exercise": exercise}, headers=auth)
    assert response.status_code == 201
    return response.get_json()["session_id"]


def send(client, auth, session_id, image_bytes):
    return client.post(f"/api/detect/sessions/{session_id}/frames", headers=auth,
                       data={"frame": (io.BytesIO(image_bytes), "frame.jpg")},
                       content_type="multipart/form-data")


def stream_video(client, auth, session_id, video):
    """Send every frame of a video as a JPEG, like the website would from the camera."""
    if not video.exists():
        pytest.skip(f"needs the dataset video {video.name}")
    cap = cv2.VideoCapture(str(video))
    result = None
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        response = send(client, auth, session_id, cv2.imencode(".jpg", frame)[1].tobytes())
        assert response.status_code == 200
        result = response.get_json()["result"]
    cap.release()
    return result


def test_detect_needs_login(client):
    assert client.post("/api/detect/sessions", json={}).status_code == 401


def test_unknown_exercise_is_rejected(client, auth):
    response = client.post("/api/detect/sessions", json={"exercise": "burpee"}, headers=auth)
    assert response.status_code == 400


def test_bad_frames_are_rejected(client, auth):
    session_id = start(client, auth)
    assert send(client, auth, session_id, b"not an image").status_code == 400
    no_file = client.post(f"/api/detect/sessions/{session_id}/frames", headers=auth)
    assert no_file.status_code == 400


def test_sessions_are_private(client, auth):
    session_id = start(client, auth)
    body = {"username": "other", "email": "other@example.com", "password": "password123"}
    other_token = client.post("/api/auth/signup", json=body).get_json()["token"]
    other = {"Authorization": f"Bearer {other_token}"}
    assert send(client, other, session_id, b"x").status_code == 404
    assert client.delete(f"/api/detect/sessions/{session_id}", headers=other).status_code == 404


def test_end_session_returns_summary_then_session_is_gone(client, auth):
    session_id = start(client, auth, "squat")
    ended = client.delete(f"/api/detect/sessions/{session_id}", headers=auth)
    assert ended.status_code == 200
    assert ended.get_json()["summary"]["exercise"] == "squat"
    assert client.delete(f"/api/detect/sessions/{session_id}", headers=auth).status_code == 404


@pytest.mark.parametrize("video, exercise, reps", [
    ("pushup/push-up_2.mp4", "pushup", 2),
    ("curl/barbell biceps curl_7.mp4", "curl", 2),
    ("squat/squat_8.mp4", "squat", 1),
])
def test_recognizes_exercise_and_counts_reps(client, auth, video, exercise, reps):
    # No exercise chosen: the classifier decides what to count. Rep counts are the
    # hand-counted values from the rep counter evaluation.
    session_id = start(client, auth)
    result = stream_video(client, auth, session_id, VIDEOS / video)
    assert result["detected_exercise"] == exercise
    assert result["counted_exercise"] == exercise
    assert result["reps"] == reps
    assert len(result["landmarks"]) == 33
    summary = client.delete(f"/api/detect/sessions/{session_id}", headers=auth).get_json()
    assert summary["summary"]["reps"] == reps

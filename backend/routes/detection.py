"""Live exercise detection: the website sends camera frames, the server answers with the
exercise, the rep count and the skeleton points. All endpoints need the login token.

POST   /api/detect/sessions              {"exercise"?}  -> 201 {"session_id", "exercise"}
POST   /api/detect/sessions/<id>/frames  form-data "frame" = JPEG/PNG image -> 200 {"result"}
DELETE /api/detect/sessions/<id>         -> 200 {"summary": {"exercise", "reps", ...}}

"exercise" is the exercise the user picked (e.g. from their workout); reps are counted for
it. Without it, reps are counted for the exercise the classifier recognizes. The website
saves the summary with POST /api/history.
"""
import cv2
import numpy as np
from flask import Blueprint, current_app, g, jsonify, request

from backend.auth import login_required
from backend.ml_engine import EXERCISES, TooManySessions

bp = Blueprint("detection", __name__, url_prefix="/api/detect")


def store():
    return current_app.extensions["detection_sessions"]


@bp.post("/sessions")
@login_required
def start_session():
    exercise = (request.get_json(silent=True) or {}).get("exercise")
    if exercise is not None and exercise not in EXERCISES:
        return jsonify(error=f"exercise must be one of: {', '.join(EXERCISES)}."), 400
    try:
        session = store().create(g.user.user_id, exercise)
    except TooManySessions:
        return jsonify(error="The server is busy. Try again in a few minutes."), 503
    return jsonify(session_id=session.session_id, exercise=exercise), 201


@bp.post("/sessions/<session_id>/frames")
@login_required
def send_frame(session_id):
    session = store().get(session_id, g.user.user_id)
    if session is None:
        return jsonify(error="Session not found (it may have expired)."), 404
    upload = request.files.get("frame")
    if upload is None:
        return jsonify(error='Send the image as form-data field "frame".'), 400
    image = cv2.imdecode(np.frombuffer(upload.read(), np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return jsonify(error="The frame is not a valid JPEG or PNG image."), 400
    return jsonify(result=session.process(image))


@bp.delete("/sessions/<session_id>")
@login_required
def end_session(session_id):
    session = store().close(session_id, g.user.user_id)
    if session is None:
        return jsonify(error="Session not found (it may have expired)."), 404
    return jsonify(summary=session.summary())

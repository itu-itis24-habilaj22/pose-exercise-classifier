"""Live exercise detection for the API: pose detection, classification and rep counting
on frames that arrive one by one from the website.

Recognizing the exercise and counting reps need memory across frames (the last 30 frames
for the LSTM, "down" or "up" for each rep counter), but each HTTP request stands alone. So
a DetectionSession keeps that state in memory for one exercise set of one user, and
SessionStore holds the open sessions.

Reuses the code in src/ (the same functions the scripts and tests use), so the backend
detects and counts exactly like the evaluated pipeline.
"""
import sys
import threading
import time
import uuid
from collections import Counter, deque
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import torch

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from counter_demo import measure  # noqa: E402
from features import normalize_keypoints  # noqa: E402
from make_sequences import MAX_GAP, SEQUENCE_LENGTH, STRIDE  # noqa: E402
from pose_demo import DEFAULT_MODEL, create_landmarker  # noqa: E402
from predict import DEFAULT_CLASSIFIER  # noqa: E402
from rep_counter import EXERCISES, make_counter  # noqa: E402
from train_lstm import load_lstm  # noqa: E402

SCALE_FRAMES = 150   # recent frames used to estimate the body size for normalization (~5 s)
VOTE_WINDOWS = 5     # the last classifications vote on the exercise (smooths single errors)
MAX_SESSIONS = 20    # each session holds a MediaPipe tracker in memory
IDLE_SECONDS = 600   # sessions without frames for 10 minutes are closed

_classifier = None
_classifier_lock = threading.Lock()


def classifier():
    """The LSTM and its class names, loaded once and shared by all sessions."""
    global _classifier
    with _classifier_lock:
        if _classifier is None:
            _classifier = load_lstm(DEFAULT_CLASSIFIER)
    return _classifier


def models_available():
    return Path(DEFAULT_MODEL).exists() and Path(DEFAULT_CLASSIFIER).exists()


class DetectionSession:
    def __init__(self, user_id, exercise=None):
        self.session_id = uuid.uuid4().hex
        self.user_id = user_id
        self.chosen_exercise = exercise  # picked by the user; None = use the classifier's
        self.model, self.classes = classifier()
        self.landmarker = create_landmarker(DEFAULT_MODEL)
        self.lock = threading.Lock()  # one frame at a time per session
        self.started = self.last_used = time.monotonic()
        self.last_timestamp_ms = -1
        self.frames = 0
        self.recent = deque(maxlen=SCALE_FRAMES)  # keypoints (33, 4) of recent frames
        self.missing_in_a_row = 0
        self.since_classified = 0
        self.votes = deque(maxlen=VOTE_WINDOWS)
        self.counters = {name: make_counter(name) for name in EXERCISES}

    def process(self, image_bgr):
        """Run one camera frame through the pipeline; returns the current result."""
        with self.lock:
            now = time.monotonic()
            self.last_used = now
            # MediaPipe's video mode needs strictly increasing timestamps.
            timestamp_ms = max(int((now - self.started) * 1000), self.last_timestamp_ms + 1)
            self.last_timestamp_ms = timestamp_ms
            height, width = image_bgr.shape[:2]
            image = mp.Image(image_format=mp.ImageFormat.SRGB,
                             data=cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
            result = self.landmarker.detect_for_video(image, timestamp_ms)
            self.frames += 1

            for name, config in EXERCISES.items():
                value = measure(result, config)
                if value is not None:
                    self.counters[name].update(value)
            self._update_keypoints(result)
            if len(self.recent) >= SEQUENCE_LENGTH and self.since_classified >= STRIDE:
                self._classify(width / height)
            return self._state(result)

    def _update_keypoints(self, result):
        if result.pose_landmarks:
            self.recent.append([[p.x, p.y, p.z, p.visibility or 0]
                                for p in result.pose_landmarks[0]])
            self.missing_in_a_row = 0
            self.since_classified += 1
        elif self.recent and self.missing_in_a_row < MAX_GAP:
            # Short gap: repeat the last pose (training filled gaps of up to MAX_GAP frames).
            self.recent.append(self.recent[-1])
            self.missing_in_a_row += 1
            self.since_classified += 1
        else:
            self.recent.clear()  # person gone: start over, like windows with gaps in training
            self.since_classified = 0

    def _classify(self, aspect_ratio):
        # The body size is estimated from the recent frames, like the per-video scale used
        # in training; then the last 30 frames go to the LSTM.
        normalized = normalize_keypoints(np.array(self.recent, dtype=float), aspect_ratio)
        window = normalized[-SEQUENCE_LENGTH:, :, :2].reshape(1, SEQUENCE_LENGTH, -1)
        with torch.no_grad():
            predicted = self.model(torch.from_numpy(window.astype(np.float32))).argmax(dim=1)
        self.votes.append(self.classes[int(predicted)])
        self.since_classified = 0

    def detected_exercise(self):
        """(exercise, share of the recent votes) or (None, None) before the first vote."""
        if not self.votes:
            return None, None
        exercise, count = Counter(self.votes).most_common(1)[0]
        return exercise, count / len(self.votes)

    def counted_exercise(self):
        return self.chosen_exercise or self.detected_exercise()[0]

    def _state(self, result):
        exercise, confidence = self.detected_exercise()
        counted = self.counted_exercise()
        landmarks = None
        if result.pose_landmarks:  # for drawing the skeleton on the website
            landmarks = [[round(p.x, 4), round(p.y, 4), round(p.visibility or 0, 3)]
                         for p in result.pose_landmarks[0]]
        return {
            "frame": self.frames,
            "person_detected": bool(result.pose_landmarks),
            "detected_exercise": exercise,
            "confidence": round(confidence, 2) if confidence is not None else None,
            "counted_exercise": counted,
            "reps": self.counters[counted].count if counted else 0,
            "form_score": None,  # form feedback comes in Phase 4
            "landmarks": landmarks,
        }

    def summary(self):
        counted = self.counted_exercise()
        return {
            "exercise": counted,
            "reps": self.counters[counted].count if counted else 0,
            "frames": self.frames,
            "duration": round(self.last_used - self.started),
        }

    def close(self):
        self.landmarker.close()


class TooManySessions(Exception):
    pass


class SessionStore:
    """The open detection sessions, shared by all requests (thread-safe).

    Sessions live in this process's memory, so the production server must run a single
    process (with several threads); see docs.
    """

    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()

    def create(self, user_id, exercise=None):
        with self.lock:
            self._close_idle()
            if len(self.sessions) >= MAX_SESSIONS:
                raise TooManySessions()
            session = DetectionSession(user_id, exercise)
            self.sessions[session.session_id] = session
            return session

    def get(self, session_id, user_id):
        """The session if it exists and belongs to this user, else None."""
        with self.lock:
            session = self.sessions.get(session_id)
        return session if session is not None and session.user_id == user_id else None

    def close(self, session_id, user_id):
        with self.lock:
            session = self.sessions.get(session_id)
            if session is None or session.user_id != user_id:
                return None
            del self.sessions[session_id]
        with session.lock:  # wait for a frame that is still being processed
            session.close()
        return session

    def close_all(self):
        """Close every session. MediaPipe trackers must be closed explicitly: if Python's
        garbage collector closes them at a random moment instead, it can deadlock."""
        with self.lock:
            sessions = list(self.sessions.values())
            self.sessions.clear()
        for session in sessions:
            with session.lock:
                session.close()

    def _close_idle(self):
        now = time.monotonic()
        for session_id, session in list(self.sessions.items()):
            if now - session.last_used > IDLE_SECONDS:
                del self.sessions[session_id]
                session.close()

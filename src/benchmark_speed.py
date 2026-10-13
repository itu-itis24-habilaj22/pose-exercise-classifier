"""Measure how long each step of the pipeline takes per frame (roadmap target: <100 ms).

For every frame of a video it times:
  1. pose detection (MediaPipe),
  2. exercise classification of the last 30 frames (LSTM, and the Random Forest baseline),
  3. rep counting (one update of the counter).

Usage (from the project root, with .venv activated):
    python src/benchmark_speed.py
    python src/benchmark_speed.py --source "data/raw_videos/curl/barbell biceps curl_52.mp4"
"""
import argparse
import time

import cv2
import joblib
import mediapipe as mp
import numpy as np
import torch

from counter_demo import measure
from features import normalize_keypoints
from make_sequences import SEQUENCE_LENGTH
from pose_demo import DEFAULT_MODEL, PROJECT_ROOT, create_landmarker
from rep_counter import EXERCISES, make_counter
from train_classifier import summary_features
from train_lstm import load_lstm

TARGET_MS = 100
DEFAULT_VIDEO = PROJECT_ROOT / "data" / "raw_videos" / "pushup" / "push-up_54.mp4"


def stats(times_s):
    ms = np.array(times_s) * 1000
    return f"mean {ms.mean():6.1f}  median {np.median(ms):6.1f}  95% {np.percentile(ms, 95):6.1f}"


def main():
    parser = argparse.ArgumentParser(description="Time each step of the pipeline per frame")
    parser.add_argument("--source", default=str(DEFAULT_VIDEO), help="path to a video file")
    parser.add_argument("--exercise", choices=EXERCISES, default="pushup",
                        help="exercise used for the rep counting step")
    args = parser.parse_args()

    lstm, _ = load_lstm(PROJECT_ROOT / "models" / "exercise_classifier_lstm.pt")
    forest = joblib.load(PROJECT_ROOT / "models" / "exercise_classifier_rf.joblib")["model"]
    forest.set_params(n_jobs=1)  # one sequence at a time: starting worker threads costs more
    torch.set_num_threads(1)     # same for PyTorch; also leaves the other cores free

    cap = cv2.VideoCapture(args.source)
    if not cap.isOpened():
        raise SystemExit(f"Could not open video: {args.source}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width, height = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    config = EXERCISES[args.exercise]
    counter = make_counter(args.exercise)

    times = {"pose": [], "lstm": [], "forest": [], "count": []}
    recent = []  # keypoints of the last SEQUENCE_LENGTH frames
    with create_landmarker(DEFAULT_MODEL) as landmarker:
        frame_index = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            start = time.perf_counter()
            result = landmarker.detect_for_video(image, int(frame_index * 1000 / fps))
            times["pose"].append(time.perf_counter() - start)
            frame_index += 1

            start = time.perf_counter()
            value = measure(result, config)
            if value is not None:
                counter.update(value)
            times["count"].append(time.perf_counter() - start)

            if not result.pose_landmarks:
                recent.clear()
                continue
            recent.append([[p.x, p.y, p.z, p.visibility or 0] for p in result.pose_landmarks[0]])
            recent = recent[-SEQUENCE_LENGTH:]
            if len(recent) < SEQUENCE_LENGTH:
                continue

            start = time.perf_counter()
            window = normalize_keypoints(np.array(recent), width / height)
            features = window[..., :2].reshape(1, SEQUENCE_LENGTH, -1).astype(np.float32)
            with torch.no_grad():
                lstm(torch.from_numpy(features))
            times["lstm"].append(time.perf_counter() - start)

            start = time.perf_counter()
            forest.predict(summary_features(features))
            times["forest"].append(time.perf_counter() - start)
    cap.release()

    print(f"Video: {args.source}  ({frame_index} frames, {int(width)}x{int(height)})\n")
    print("Time per frame in ms:")
    print(f"  pose detection         {stats(times['pose'])}")
    print(f"  classify (LSTM)        {stats(times['lstm'])}")
    print(f"  classify (Rand. Forest) {stats(times['forest'])}")
    print(f"  rep counting           {stats(times['count'])}")
    total = np.median(times["pose"]) + np.median(times["lstm"]) + np.median(times["count"])
    print(f"\nPipeline with LSTM (median): {total * 1000:.1f} ms per frame "
          f"= about {1 / total:.0f} frames per second")
    verdict = "meets" if total * 1000 < TARGET_MS else "does NOT meet"
    print(f"This {verdict} the roadmap target of <{TARGET_MS} ms per frame.")


if __name__ == "__main__":
    main()

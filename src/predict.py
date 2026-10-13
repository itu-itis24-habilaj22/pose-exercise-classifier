"""Recognize the exercise in a video and count its reps: the full pipeline in one script.

  1. pose detection on every frame (MediaPipe),
  2. the video is cut into 30-frame sequences, exactly as for training, and the LSTM
     classifies each one; the exercise with the most votes wins,
  3. the rep counter for that exercise counts the reps.

Usage (from the project root, with .venv activated):
    python src/predict.py data/raw_videos/pushup/push-up_2.mp4
"""
import argparse
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import torch

from counter_demo import measure
from features import normalize_keypoints
from make_sequences import fill_short_gaps, make_windows
from pose_demo import DEFAULT_MODEL, PROJECT_ROOT, create_landmarker
from rep_counter import EXERCISES, make_counter
from train_lstm import load_lstm

DEFAULT_CLASSIFIER = PROJECT_ROOT / "models" / "exercise_classifier_lstm.pt"


def analyze_video(video_path, model_path=DEFAULT_MODEL):
    """One pass of pose detection over the video.

    Returns (keypoints, aspect_ratio, values): keypoints is (frames, 33, 4) with NaN where
    no person was found, and values[exercise] holds what that exercise's rep counter
    measures in each frame (None where not visible). All exercises are measured because
    we only know which one it is after classifying.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise SystemExit(f"Could not open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    aspect_ratio = cap.get(cv2.CAP_PROP_FRAME_WIDTH) / cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    keypoints, values = [], {exercise: [] for exercise in EXERCISES}
    with create_landmarker(model_path) as landmarker:
        frame_index = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            image = mp.Image(image_format=mp.ImageFormat.SRGB,
                             data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            result = landmarker.detect_for_video(image, int(frame_index * 1000 / fps))
            frame_index += 1
            if result.pose_landmarks:
                keypoints.append([[p.x, p.y, p.z, p.visibility or 0]
                                  for p in result.pose_landmarks[0]])
            else:
                keypoints.append(np.full((33, 4), np.nan))
            for exercise, config in EXERCISES.items():
                values[exercise].append(measure(result, config))
    cap.release()
    return np.array(keypoints, dtype=float), aspect_ratio, values


def classify(keypoints, aspect_ratio, model, classes):
    """Vote over all 30-frame sequences; returns (exercise, votes per exercise)."""
    normalized = normalize_keypoints(keypoints, aspect_ratio)
    features = normalized[..., :2].reshape(len(normalized), -1)
    windows = make_windows(fill_short_gaps(features)).astype(np.float32)
    if len(windows) == 0:
        return None, {}
    with torch.no_grad():
        predicted = model(torch.from_numpy(windows)).argmax(dim=1).numpy()
    votes = {name: int((predicted == i).sum()) for i, name in enumerate(classes)}
    return max(votes, key=votes.get), votes


def count_reps(values, exercise):
    counter = make_counter(exercise)
    for value in values:
        if value is not None:
            counter.update(value)
    return counter.count


def main():
    parser = argparse.ArgumentParser(description="Recognize the exercise and count reps")
    parser.add_argument("video", type=Path, help="path to a video file")
    parser.add_argument("--classifier", type=Path, default=DEFAULT_CLASSIFIER,
                        help="LSTM saved by train_lstm.py")
    args = parser.parse_args()

    model, classes = load_lstm(args.classifier)
    keypoints, aspect_ratio, values = analyze_video(args.video)
    exercise, votes = classify(keypoints, aspect_ratio, model, classes)
    if exercise is None:
        raise SystemExit("No person found in 30 frames in a row: can't classify this video.")

    total = sum(votes.values())
    print(f"Video:    {args.video.name}  ({len(keypoints)} frames)")
    print(f"Exercise: {exercise}  ({votes[exercise]} of {total} sequences, "
          f"{votes[exercise] / total:.0%})")
    print("Votes:    " + ", ".join(f"{name} {n}" for name, n in votes.items()))
    print(f"Reps:     {count_reps(values[exercise], exercise)}")


if __name__ == "__main__":
    main()

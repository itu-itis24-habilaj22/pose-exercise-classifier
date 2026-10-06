"""Detect a person's pose in a webcam feed or video file and draw the skeleton.

Usage (from the project root, with .venv activated):
    python src/pose_demo.py                      # webcam
    python src/pose_demo.py --source path/to/video.mp4

Press Q or Esc to quit.
"""

import argparse
import time
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = PROJECT_ROOT / "models" / "pose_landmarker_full.task"
CONNECTIONS = vision.PoseLandmarksConnections.POSE_LANDMARKS


def create_landmarker(model_path):
    options = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
    )
    return vision.PoseLandmarker.create_from_options(options)


def draw_pose(frame, landmarks, min_visibility=0.5):
    """Draw the skeleton (lines) and joints (dots) on the frame."""
    h, w = frame.shape[:2]
    points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    visible = [(lm.visibility or 0) >= min_visibility for lm in landmarks]

    for conn in CONNECTIONS:
        if visible[conn.start] and visible[conn.end]:
            cv2.line(frame, points[conn.start], points[conn.end], (255, 255, 255), 2)
    for point, is_visible in zip(points, visible):
        if is_visible:
            cv2.circle(frame, point, 4, (0, 200, 255), -1)


def main():
    parser = argparse.ArgumentParser(description="Pose detection demo")
    parser.add_argument("--source", default="0",
                        help="webcam index (e.g. 0) or path to a video file")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="path to the .task model")
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise SystemExit(f"Could not open video source: {args.source}")

    is_webcam = isinstance(source, int)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    start = time.monotonic()
    frame_index = 0

    with create_landmarker(args.model) as landmarker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if is_webcam:
                frame = cv2.flip(frame, 1)  # mirror view feels natural on a webcam

            # VIDEO mode needs a timestamp (ms) that increases every frame.
            if is_webcam:
                timestamp_ms = int((time.monotonic() - start) * 1000)
            else:
                timestamp_ms = int(frame_index * 1000 / fps)
            frame_index += 1

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            if result.pose_landmarks:
                draw_pose(frame, result.pose_landmarks[0])
                status = "Pose detected"
            else:
                status = "No person detected"
            cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0), 2)

            cv2.imshow("Pose demo (Q to quit)", frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

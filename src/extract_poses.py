"""Extract pose keypoints from a video and save them as a CSV table.

Usage (from the project root, with .venv activated):
    python src/extract_poses.py data/samples/video.mp4
    python src/extract_poses.py data/samples/video.mp4 --output data/poses/my_video.csv

Each CSV row is one video frame. For each of the 33 MediaPipe landmarks there
are 4 columns: x and y (position as a fraction of the image width/height,
0 to 1), z (depth, relative to the hips) and visibility (0 to 1). Frames where
no person was detected are kept, with empty values. The image_width and
image_height columns record the video size (needed to normalize x vs. y).
"""

import argparse
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
from tqdm import tqdm

from pose_demo import DEFAULT_MODEL, PROJECT_ROOT, create_landmarker

# The 33 MediaPipe Pose landmarks, in index order (0 = nose, ..., 32 = right_foot_index).
LANDMARK_NAMES = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer", "left_ear", "right_ear",
    "mouth_left", "mouth_right", "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow", "left_wrist", "right_wrist",
    "left_pinky", "right_pinky", "left_index", "right_index",
    "left_thumb", "right_thumb", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
    "left_heel", "right_heel", "left_foot_index", "right_foot_index",
]
VALUES = ["x", "y", "z", "visibility"]


def extract_keypoints(video_path, model_path=DEFAULT_MODEL):
    """Run pose detection on every frame.

    Returns (keypoints, fps, (width, height)): keypoints is a numpy array of shape
    (frames, 33, 4) holding x, y, z, visibility; NaN where no person was found.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise SystemExit(f"Could not open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    frames = []
    with create_landmarker(model_path) as landmarker:
        for frame_index in tqdm(range(total), desc="Extracting", unit="frame"):
            ok, frame = cap.read()
            if not ok:  # the frame count in the file header can be slightly off
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect_for_video(mp_image, int(frame_index * 1000 / fps))

            if result.pose_landmarks:
                points = [[lm.x, lm.y, lm.z, lm.visibility or 0]
                          for lm in result.pose_landmarks[0]]
            else:
                points = np.full((len(LANDMARK_NAMES), len(VALUES)), np.nan)
            frames.append(points)
    cap.release()

    keypoints = np.array(frames, dtype=float).reshape(-1, len(LANDMARK_NAMES), len(VALUES))
    return keypoints, fps, size


KEYPOINT_COLUMNS = [f"{name}_{value}" for name in LANDMARK_NAMES for value in VALUES]


def keypoints_to_table(keypoints, fps, size):
    """Flatten (frames, 33, 4) into a table with one row per frame."""
    table = pd.DataFrame(keypoints.reshape(len(keypoints), -1), columns=KEYPOINT_COLUMNS)
    table.insert(0, "frame", range(len(keypoints)))
    table.insert(1, "time_s", (table["frame"] / fps).round(3))
    table.insert(2, "image_width", size[0])
    table.insert(3, "image_height", size[1])
    return table


def load_keypoints(csv_path):
    """Read a CSV saved by this script back into (table, keypoints array)."""
    table = pd.read_csv(csv_path)
    keypoints = table[KEYPOINT_COLUMNS].to_numpy().reshape(-1, len(LANDMARK_NAMES), len(VALUES))
    return table, keypoints


def main():
    parser = argparse.ArgumentParser(description="Extract pose keypoints to CSV")
    parser.add_argument("video", type=Path, help="path to a video file")
    parser.add_argument("--output", type=Path,
                        help="CSV path (default: data/poses/<video name>.csv)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="path to the .task model")
    args = parser.parse_args()

    if not args.video.is_file():
        raise SystemExit(f"Video file not found: {args.video}")
    output = args.output or PROJECT_ROOT / "data" / "poses" / f"{args.video.stem}.csv"

    keypoints, fps, size = extract_keypoints(args.video, args.model)
    table = keypoints_to_table(keypoints, fps, size)
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False, float_format="%.5f")

    detected = int(table["nose_x"].notna().sum())
    print(f"Numpy array shape: {keypoints.shape}  (frames, landmarks, values)")
    print(f"Person detected in {detected}/{len(table)} frames "
          f"({100 * detected / max(len(table), 1):.0f}%)")
    print(f"Saved {len(table)} rows x {table.shape[1]} columns to {output}")


if __name__ == "__main__":
    main()

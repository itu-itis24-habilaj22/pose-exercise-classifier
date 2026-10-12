"""Cut the kept videos into fixed-length pose sequences: the input for the classifier.

For every video marked keep=True in data/poses/quality.csv:
  1. load its keypoints and normalize them (hip-centered, torso-scaled),
  2. keep the x and y of the 33 landmarks -> 66 numbers per frame,
  3. fill gaps of up to MAX_GAP frames without a detected person by interpolation,
  4. slide a window of SEQUENCE_LENGTH frames along the video, moving STRIDE frames
     each time; windows that still contain a missing frame are skipped.

Saves data/sequences.npz with:
  X       (sequences, SEQUENCE_LENGTH, 66)  the pose sequences
  y       (sequences,)                       exercise index into `classes`
  video   (sequences,)                       source video, so train/test can be split
                                             by video (windows of one video overlap)
  classes the exercise names

Usage (from the project root, with .venv activated):
    python src/make_sequences.py
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from extract_poses import load_keypoints
from features import normalize_keypoints

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEQUENCE_LENGTH = 30
STRIDE = 15
MAX_GAP = 5  # missing frames in a row that may be filled in (~0.2 s)


def pose_features(table, keypoints):
    """(frames, 33, 4) keypoints -> (frames, 66) normalized x, y per frame."""
    aspect_ratio = table["image_width"].iloc[0] / table["image_height"].iloc[0]
    normalized = normalize_keypoints(keypoints, aspect_ratio)
    return normalized[..., :2].reshape(len(normalized), -1)


def fill_short_gaps(features, max_gap=MAX_GAP):
    """Fill runs of up to max_gap missing frames by linear interpolation.

    Longer gaps, and gaps at the start or end of the video, are left as NaN.
    """
    filled = features.copy()
    missing = np.isnan(features).any(axis=1)
    frame = 0
    while frame < len(features):
        if not missing[frame]:
            frame += 1
            continue
        start = frame
        while frame < len(features) and missing[frame]:
            frame += 1
        before, after = start - 1, frame  # the detected frames around the gap
        if before >= 0 and after < len(features) and frame - start <= max_gap:
            weights = np.arange(1, frame - start + 1)[:, None] / (after - before)
            filled[start:frame] = (1 - weights) * features[before] + weights * features[after]
    return filled


def make_windows(features, length=SEQUENCE_LENGTH, stride=STRIDE):
    """Slide a window over (frames, n) features; skip windows that contain NaN frames."""
    windows = [features[start:start + length]
               for start in range(0, len(features) - length + 1, stride)]
    windows = [w for w in windows if not np.isnan(w).any()]
    return np.array(windows).reshape(-1, length, features.shape[1])


def main():
    parser = argparse.ArgumentParser(description="Make pose sequences for training")
    parser.add_argument("--poses", type=Path, default=PROJECT_ROOT / "data" / "poses")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "data" / "sequences.npz")
    args = parser.parse_args()

    quality = pd.read_csv(args.poses / "quality.csv")
    kept = quality[quality["keep"]]
    classes = sorted(kept["exercise"].unique())

    X, y, videos = [], [], []
    for _, row in kept.iterrows():
        table, keypoints = load_keypoints(args.poses / row["exercise"] / f"{row['video']}.csv")
        windows = make_windows(fill_short_gaps(pose_features(table, keypoints)))
        X.append(windows)
        y += [classes.index(row["exercise"])] * len(windows)
        videos += [row["video"]] * len(windows)

    X = np.concatenate(X).astype(np.float32)
    y = np.array(y)
    np.savez(args.output, X=X, y=y, video=np.array(videos), classes=np.array(classes))

    print(f"{'exercise':8s} {'videos':>6s} {'sequences':>9s}")
    for i, name in enumerate(classes):
        n_videos = len(set(np.array(videos)[y == i]))
        print(f"{name:8s} {n_videos:6d} {(y == i).sum():9d}")
    print(f"\nX shape: {X.shape}  (sequences, frames, features)")
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()

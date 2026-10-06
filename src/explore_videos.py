"""Summarize a folder of exercise videos: resolution, FPS, length, orientation.

Expects one subfolder per exercise, e.g. data/raw_videos/squat/*.mp4.

Usage (from the project root, with .venv activated):
    python src/explore_videos.py
    python src/explore_videos.py --folder data/raw_videos
"""

import argparse
from pathlib import Path

import cv2
import pandas as pd

from pose_demo import PROJECT_ROOT

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


def find_videos(folder):
    """Yield (exercise, path) for every video in folder/<exercise>/."""
    for exercise_dir in sorted(p for p in folder.iterdir() if p.is_dir()):
        for path in sorted(exercise_dir.iterdir()):
            if path.suffix.lower() in VIDEO_EXTENSIONS:  # .MOV and .mov both count
                yield exercise_dir.name, path


def video_info(path):
    """Read a video's properties from its header, without decoding every frame."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"readable": False}
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return {
        "readable": True,
        "width": width,
        "height": height,
        "orientation": "portrait" if height > width else "landscape",
        "fps": round(fps, 1),
        "frames": frames,
        "seconds": round(frames / fps, 1) if fps else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Summarize exercise videos")
    parser.add_argument("--folder", type=Path, default=PROJECT_ROOT / "data" / "raw_videos")
    args = parser.parse_args()

    rows = []
    for exercise, path in find_videos(args.folder):
        rows.append({"exercise": exercise, "file": path.name,
                     "size_mb": round(path.stat().st_size / 1e6, 1), **video_info(path)})
    if not rows:
        raise SystemExit(f"No videos found in {args.folder}/<exercise>/")

    table = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(table.to_string(index=False))

    unreadable = table[~table["readable"]]
    if len(unreadable):
        print(f"\nWARNING: OpenCV could not open {len(unreadable)} file(s):",
              ", ".join(unreadable["file"]))

    readable = table[table["readable"]]
    print("\nPer exercise:")
    summary = readable.groupby("exercise").agg(
        videos=("file", "count"),
        total_seconds=("seconds", "sum"),
        shortest_s=("seconds", "min"),
        longest_s=("seconds", "max"),
        portrait=("orientation", lambda o: (o == "portrait").sum()),
    )
    print(summary.to_string())
    print(f"\nTotal: {len(readable)} videos, {readable['seconds'].sum() / 60:.1f} minutes")


if __name__ == "__main__":
    main()

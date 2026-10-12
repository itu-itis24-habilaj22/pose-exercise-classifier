"""Check the quality of extracted poses and decide which videos to keep for training.

A high detection rate isn't enough: a person can be "detected" while the joints we need
are out of frame or hidden. So a video is kept only if:
  - a person is detected in at least MIN_DETECTION of its frames, and
  - the hips, shoulders (needed for normalization) and the exercise's own joint
    (knee for squats, elbow for push-ups and curls) have a mean visibility of at
    least MIN_VISIBILITY. For each joint the better of the left/right side is used.

Writes data/poses/quality.csv with one row per video and a `keep` column.

Usage (from the project root, with .venv activated):
    python src/check_quality.py
"""
import argparse
from pathlib import Path

import pandas as pd

from rep_counter import EXERCISES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIN_DETECTION = 0.8
MIN_VISIBILITY = 0.5


def joint_visibility(table, joint):
    """Mean visibility of a joint, using the more visible side in each frame."""
    sides = table[[f"left_{joint}_visibility", f"right_{joint}_visibility"]]
    return sides.max(axis=1).mean()


def check_video(csv_path, exercise):
    table = pd.read_csv(csv_path)
    row = {
        "exercise": exercise,
        "video": csv_path.stem,
        "frames": len(table),
        "detection": table["nose_x"].notna().mean(),
    }
    joints = ["hip", "shoulder", EXERCISES[exercise]["joint"]]
    for joint in joints:
        row[f"{joint}_vis"] = joint_visibility(table, joint)

    problems = []
    if row["detection"] < MIN_DETECTION:
        problems.append(f"detected in {row['detection']:.0%} of frames")
    for joint in joints:
        if row[f"{joint}_vis"] < MIN_VISIBILITY:
            problems.append(f"{joint} visibility {row[f'{joint}_vis']:.2f}")
    row["keep"] = not problems
    row["problems"] = "; ".join(problems)
    return row


def main():
    parser = argparse.ArgumentParser(description="Check pose quality per video")
    parser.add_argument("--poses", type=Path, default=PROJECT_ROOT / "data" / "poses")
    args = parser.parse_args()

    rows = [check_video(csv_path, exercise_dir.name)
            for exercise_dir in sorted(args.poses.iterdir())
            if exercise_dir.is_dir() and exercise_dir.name in EXERCISES
            for csv_path in sorted(exercise_dir.glob("*.csv"))]
    report = pd.DataFrame(rows)
    output = args.poses / "quality.csv"
    report.to_csv(output, index=False, float_format="%.3f")

    print("Removed videos:")
    for _, r in report[~report["keep"]].iterrows():
        print(f"  {r['exercise']:7s} {r['video']:28s} {r['problems']}")
    print("\nVideos kept per exercise:")
    summary = report.groupby("exercise")["keep"].agg(total="size", kept="sum")
    print(summary.to_string())
    print(f"\nSaved report to {output}")


if __name__ == "__main__":
    main()

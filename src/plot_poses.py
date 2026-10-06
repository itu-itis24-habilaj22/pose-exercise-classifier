"""Plot keypoints from an extracted pose CSV over time, before and after normalization.

Usage (from the project root, with .venv activated):
    python src/plot_poses.py data/poses/video.csv
    python src/plot_poses.py data/poses/video.csv --landmarks right_knee right_wrist

Saves the figure next to the CSV as <name>_plot.png and opens it in a window.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from extract_poses import LANDMARK_NAMES, load_keypoints
from features import normalize_keypoints

COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # one fixed color per landmark


def main():
    parser = argparse.ArgumentParser(description="Plot pose keypoints over time")
    parser.add_argument("csv", type=Path, help="CSV made by extract_poses.py")
    parser.add_argument("--landmarks", nargs="+", choices=LANDMARK_NAMES,
                        default=["left_shoulder", "left_wrist", "left_knee"],
                        help=f"up to {len(COLORS)} landmark names")
    args = parser.parse_args()
    if len(args.landmarks) > len(COLORS):
        raise SystemExit(f"Plot at most {len(COLORS)} landmarks at once.")

    table, keypoints = load_keypoints(args.csv)
    aspect = table["image_width"].iloc[0] / table["image_height"].iloc[0]
    normalized = normalize_keypoints(keypoints, aspect)
    time_s = table["time_s"]

    # Two charts stacked, sharing the time axis: raw values on top, normalized below.
    fig, (raw_ax, norm_ax) = plt.subplots(2, 1, sharex=True, figsize=(11, 7))
    for name, color in zip(args.landmarks, COLORS):
        i = LANDMARK_NAMES.index(name)
        raw_ax.plot(time_s, keypoints[:, i, 1], color=color, linewidth=2, label=name)
        norm_ax.plot(time_s, normalized[:, i, 1], color=color, linewidth=2, label=name)

    raw_ax.set_title("Raw: y position in the image (0 = top edge, 1 = bottom edge)", loc="left")
    raw_ax.set_ylabel("fraction of image height")
    norm_ax.set_title("Normalized: height relative to the hip center, in torso lengths",
                      loc="left")
    norm_ax.set_ylabel("torso lengths")
    norm_ax.set_xlabel("time (s)")
    norm_ax.axhline(0, color="#888888", linewidth=1)  # the hip center

    for ax in (raw_ax, norm_ax):
        ax.invert_yaxis()  # image y grows downward; flip it so "up" in the plot is up
        ax.grid(alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False)

    fig.tight_layout()
    output = args.csv.with_name(f"{args.csv.stem}_plot.png")
    fig.savefig(output, dpi=120)
    print(f"Saved {output}")
    plt.show()


if __name__ == "__main__":
    main()

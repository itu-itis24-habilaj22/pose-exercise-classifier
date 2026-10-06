"""OpenCV basics: the core image operations used later on video frames.

Usage (from the project root, with .venv activated):
    python src/opencv_image_basics.py path/to/photo.jpg

Shows the original, grayscale and edge images side by side, and saves the
result next to the input as <name>_basics.jpg. Press any key to close.
"""

import argparse
from pathlib import Path

import cv2
import numpy as np

SIZE = (640, 480)  # (width, height). Note: OpenCV sizes are width first.


def process(image):
    """Run the basic operations and return each intermediate image."""
    # 1. Resize so every image has the same size, whatever the camera produced.
    resized = cv2.resize(image, SIZE)

    # 2. Grayscale: 3 color channels (OpenCV stores them as Blue, Green, Red)
    #    become 1 channel of brightness. Many algorithms only need brightness.
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # 3. Canny edge detection: marks pixels where brightness changes sharply.
    #    Gradients below 100 are ignored; above 200 are always edges; in between
    #    they count only if connected to a strong edge.
    edges = cv2.Canny(gray, 100, 200)

    return resized, gray, edges


def side_by_side(resized, gray, edges):
    """Join the three images horizontally, each with a label."""
    # np.hstack needs the same number of channels, so turn the 1-channel
    # images back into 3 channels (they still look gray).
    panels = [resized,
              cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR),
              cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)]
    for panel, label in zip(panels, ["Original", "Grayscale", "Edges (Canny)"]):
        cv2.putText(panel, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (0, 255, 0), 2)
    return np.hstack(panels)


def main():
    parser = argparse.ArgumentParser(description="OpenCV image basics")
    parser.add_argument("image", type=Path, help="path to an image file")
    args = parser.parse_args()

    # cv2.imread does not raise an error for a bad path, it returns None.
    image = cv2.imread(str(args.image))
    if image is None:
        raise SystemExit(f"Could not read image: {args.image}")
    print(f"Loaded {args.image.name}: {image.shape[1]}x{image.shape[0]} pixels, "
          f"{image.shape[2]} channels")

    result = side_by_side(*process(image))

    output = args.image.with_name(f"{args.image.stem}_basics.jpg")
    cv2.imwrite(str(output), result)
    print(f"Saved {output}")

    # The window is 1920 px wide, so show it at half size to fit the screen.
    cv2.imshow("OpenCV basics (any key to close)",
               cv2.resize(result, None, fx=0.5, fy=0.5))
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

"""OpenCV basics: read a video (or webcam) frame by frame and display it.

Usage (from the project root, with .venv activated):
    python src/opencv_video_basics.py                         # webcam
    python src/opencv_video_basics.py data/samples/video.mp4  # video file

Press Q or Esc to quit, Space to pause.
"""

import argparse
import time
from pathlib import Path

import cv2


def open_source(source):
    """Open a webcam (a number like "0") or a video file, with clear errors."""
    if source.isdigit():
        cap = cv2.VideoCapture(int(source))
        if not cap.isOpened():
            raise SystemExit(f"Could not open webcam {source}. Is another app using it?")
        return cap

    # cv2.VideoCapture does not raise an error for a missing file, it just
    # fails to read frames, so check that the file exists first.
    if not Path(source).is_file():
        raise SystemExit(f"Video file not found: {source}")
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise SystemExit(f"Could not open video (unsupported format?): {source}")
    return cap


def main():
    parser = argparse.ArgumentParser(description="OpenCV video basics")
    parser.add_argument("source", nargs="?", default="0",
                        help="webcam index (default 0) or path to a video file")
    args = parser.parse_args()

    cap = open_source(args.source)
    is_webcam = args.source.isdigit()

    # A video is a sequence of images (frames). Ask OpenCV about it.
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30  # some webcams report 0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 0 or -1 for a webcam
    print(f"Opened {args.source}: {width}x{height}, {video_fps:.0f} FPS"
          + ("" if is_webcam else f", {total} frames ({total / video_fps:.1f} s)"))

    # waitKey(delay) waits `delay` ms for a key. For a file, wait one frame's
    # duration so it plays at normal speed; a webcam already delivers frames
    # in real time, so 1 ms is enough.
    delay = 1 if is_webcam else max(1, int(1000 / video_fps))

    frame_count = 0
    last_time = time.perf_counter()
    fps = 0.0
    paused = False

    while True:
        if not paused:
            ok, frame = cap.read()  # ok is False when the video ends
            if not ok:
                print("End of video.")
                break
            frame_count += 1

            # Measured FPS: how many frames per second we actually display.
            # Smoothed so the number doesn't jump around every frame.
            now = time.perf_counter()
            fps = 0.9 * fps + 0.1 * (1 / (now - last_time))
            last_time = now

            frame_text = f"Frame: {frame_count}" + (f"/{total}" if total > 0 else "")
            cv2.putText(frame, frame_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 65), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0), 2)
            cv2.imshow("Video basics (Q quit, Space pause)", frame)

        key = cv2.waitKey(delay) & 0xFF
        if key in (ord("q"), 27):  # 27 = Esc
            break
        if key == ord(" "):
            paused = not paused

    # Always release the camera/file and close windows, or the webcam
    # can stay "in use" for other programs.
    cap.release()
    cv2.destroyAllWindows()
    print(f"Displayed {frame_count} frames.")


if __name__ == "__main__":
    main()

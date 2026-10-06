"""Live rep counter: shows the joint angle and counts reps for one exercise.

Usage (from the project root, with .venv activated):
    python src/counter_demo.py --exercise squat
    python src/counter_demo.py --exercise curl --source path/to/video.mp4

Press R to reset the count, Q or Esc to quit.
"""

import argparse
import time

import cv2
import mediapipe as mp

from features import joint_angle
from pose_demo import DEFAULT_MODEL, create_landmarker, draw_pose
from rep_counter import EXERCISES, RepCounter

MIN_VISIBILITY = 0.5


def draw_panel(frame, exercise, counter, angle):
    cv2.rectangle(frame, (0, 0), (300, 120), (40, 40, 40), -1)
    cv2.putText(frame, exercise.upper(), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (255, 255, 255), 2)
    cv2.putText(frame, f"Reps: {counter.count}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX,
                1.2, (0, 255, 0), 3)
    angle_text = f"{angle:.0f} deg" if angle is not None else "-- (not visible)"
    cv2.putText(frame, f"Angle: {angle_text}  [{counter.stage}]", (10, 105),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 1)


def main():
    parser = argparse.ArgumentParser(description="Live rep counter")
    parser.add_argument("--exercise", choices=EXERCISES, default="squat")
    parser.add_argument("--source", default="0",
                        help="webcam index (e.g. 0) or path to a video file")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="path to the .task model")
    args = parser.parse_args()

    config = EXERCISES[args.exercise]
    counter = RepCounter(config["down_angle"], config["up_angle"])

    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise SystemExit(f"Could not open video source: {args.source}")

    is_webcam = isinstance(source, int)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    start = time.monotonic()
    frame_index = 0
    seen_angles = []

    with create_landmarker(args.model) as landmarker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if is_webcam:
                frame = cv2.flip(frame, 1)
                timestamp_ms = int((time.monotonic() - start) * 1000)
            else:
                timestamp_ms = int(frame_index * 1000 / fps)
            frame_index += 1

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            angle = None
            if result.pose_landmarks:
                draw_pose(frame, result.pose_landmarks[0])
                angle, visibility = joint_angle(result.pose_world_landmarks[0],
                                                result.pose_landmarks[0], config["joint"])
                if visibility >= MIN_VISIBILITY:
                    counter.update(angle)
                    seen_angles.append(angle)
                else:
                    angle = None

            draw_panel(frame, args.exercise, counter, angle)
            cv2.imshow("Rep counter (R reset, Q quit)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("r"):
                counter.reset()

    cap.release()
    cv2.destroyAllWindows()
    print(f"Final count: {counter.count} {args.exercise} reps")
    if seen_angles:
        print(f"{config['joint'].capitalize()} angle range: "
              f"lowest {min(seen_angles):.0f} deg, highest {max(seen_angles):.0f} deg "
              f"(rep counts below {config['down_angle']}, then above {config['up_angle']})")
    else:
        print(f"The {config['joint']} was never clearly visible. Step back so it's in frame.")


if __name__ == "__main__":
    main()

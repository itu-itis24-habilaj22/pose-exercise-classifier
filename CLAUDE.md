# Pose-Based Exercise Classifier and Rep Counter

Graduation project. The user is learning as they go: explain one step at a time, wait for them
to confirm before moving on, and let them run git commands themselves.

## Environment
- Windows, PowerShell, VS Code.
- Python 3.12 virtual environment in `.venv` (system default is 3.14, which MediaPipe may not support).
  Activate with `.venv\Scripts\activate`.
- GitHub: https://github.com/itu-itis24-habilaj22/pose-exercise-classifier (private, branch `main`).
- MediaPipe 1.0.1: the legacy `mp.solutions` API is gone. Use the Tasks API
  (`mediapipe.tasks.python.vision.PoseLandmarker`) with `models/pose_landmarker_full.task`.

## Code
- `src/pose_demo.py`: webcam/video pose detection and skeleton drawing (works, committed).
- `src/features.py`: joint angles from world landmarks; visibility from image landmarks.
- `src/rep_counter.py`: `RepCounter` with down/up angle thresholds; `EXERCISES` config
  (squat, pushup, curl).
- `src/counter_demo.py`: live rep counter; prints the angle range seen on exit.
- Tests: `python -m pytest` (tests/conftest.py adds `src/` to the path).

## Progress
- Steps 1–9 done: git, GitHub repo, Python 3.12 venv, requirements, pose model, pose demo pushed.
- Step 10 done: angle + rep counter code written, tests passing. NOT yet committed.
- Step 11 done: live squat test counted 5/5 (knee range 31–170 deg); thresholds 100/160 kept.
- Next: commit step 10/11 work, then build the exercise classifier (collect labeled videos,
  extract poses to `data/poses`, features, train in `notebooks/`, save to `models/`).

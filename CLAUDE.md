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
- Step 12 done: step 10/11 work committed and pushed (4901a6c).
- The user follows a roadmap (GRADUATION_PROJECT_ROADMAP.md): only do the current phase, don't
  build ahead. Roadmap says to use public datasets before recording our own videos.
- Roadmap status: Phase 1.1, 1.2 and 1.4 step 1 done; rep counter (Phase 2.1) done early.
  1.3 done: `src/opencv_image_basics.py` (resize, gray, Canny) and `src/opencv_video_basics.py`
  (frame count, FPS, pause) both tested by the user on webcam and on files in `data/samples/`
  (git-ignored). Committed (432c640).
  1.4 step 2 part 1 done: `src/extract_poses.py` (video → (frames,33,4) array → CSV in
  `data/poses/`), user ran it on data/samples/video.mp4: 705/705 frames detected. Not committed.
  1.4 step 2 part 2 written: `normalize_keypoints` in features.py (aspect fix, hip-centered,
  torso-scaled; tests in tests/test_normalize.py), CSV now has image_width/height columns,
  `src/plot_poses.py` plots raw vs normalized y. User ran both: plot shows 5 clear wrist reps.
  Phase 1.4 complete, committed (c571f5e).
  1.5 (current): chose Kaggle "Workout/Exercises Video" (hasyimabdillah). Downloaded to
  `C:\Users\Favi\Downloads\archive.zip` (4.6 GB, 22 exercise folders, 652 videos, mp4 + mov;
  squat 29, push-up 56, barbell biceps curl 62). 5 random videos each copied to
  `data/raw_videos/{squat,pushup,curl}/`. `src/explore_videos.py` summarizes them: all readable,
  all landscape (720p/1080p), FPS mixed 24/30, very short (1.8–21.9 s, 1.5 min total).
  `extract_poses.py` now also takes a folder (→ `data/poses/<exercise>/<video>.csv`, skips done
  ones, flags <80% detection). User ran it: all 15 extracted (85–100% detected). But detection %
  hides problems: curl_58 hips vis 0.11 (likely close-up, breaks hip-based normalization),
  curl_27 elbows 0.48. Later: filter videos by key-joint visibility, not just detection.
  Next: user views curl_58 with pose_demo, commits; then Phase 1 is done. Alternatives noted: UCF101 (6.5 GB), RepCount (rep labels,
  for later counting evaluation), Mendeley multi-view 7-exercise good/bad-form set.
  Remaining Phase 1: 1.5 public dataset.
- Later (Phase 2.2+): build the exercise classifier (collect labeled videos,
  extract poses to `data/poses`, features, train in `notebooks/`, save to `models/`).

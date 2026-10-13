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
- `src/copy_dataset.py`: copies squat/push-up/curl folders from the Kaggle zip to data/raw_videos.
- `src/check_quality.py`: per-video detection/visibility check → data/poses/quality.csv (`keep`).
- `src/make_sequences.py`: kept videos → 30-frame pose windows in data/sequences.npz.
- `src/train_classifier.py`: baseline Random Forest, split by video, saves to models/.
- Tests: `python -m pytest` (tests/conftest.py adds `src/` to the path).

## Progress
- Steps 1–9 done: git, GitHub repo, Python 3.12 venv, requirements, pose model, pose demo pushed.
- Step 10 done: angle + rep counter code written, tests passing. NOT yet committed.
- Step 11 done: live squat test counted 5/5 (knee range 31–170 deg); thresholds 100/160 kept.
- Step 12 done: step 10/11 work committed and pushed (4901a6c).
- FINAL ROADMAP (2026-10-13): ~/Downloads/FINAL_ROADMAP_v2_COMPLETE.md supersedes all earlier
  ones. Same phases plus: curls officially the 3rd exercise; freemium (free/premium tiers,
  Stripe in 4D); live voice guidance (Web Speech API, Phase 3D); schema adds
  subscription_tier, stripe_customer_id, joints_to_track, voice_enabled. New 2A items:
  "handle different speeds", "handle partial visibility", "optimize for mobile inference",
  deliverable "training notebook". Still says Keras .h5 (user chose PyTorch).
- Previous roadmap (2026-10-12): ~/Downloads/FINAL_GRADUATION_PROJECT_ROADMAP.md — a
  full-stack "Personal Trainer AI" (Flask + PostgreSQL backend, React frontend, deploy). Advisor:
  Prof. Dr. Mehmet Keskinöz. Phase 2A = ML (rep counter >95% on push-ups; classifier pushup/
  squat/burpee, 30+ videos each, >80%; save model, <100 ms/frame, prediction script, model docs).
  Phase 2B = Flask API + DB + auth + /api/detect. Phase 3 React, Phase 4 features/deploy.
  The old roadmap (GRADUATION_PROJECT_ROADMAP.md) is superseded.
  User decided: keep pushup/squat/curl (not burpees); 26 squat videos is enough (no more data).
  User decided: keep PyTorch (.pt), not Keras .h5. Push-up rep counter test: user's eye counts
  43:1, 2:2, 49:3, 29:5, 54:19 (9+10) = 30. Old 90/150 got 13; rep bottoms are often 95–105°.
  Changed pushup to 110/140 → 30/30 (simulated on recorded angles). Validated on 5 new videos
  (23:1, 25:2, 32:5, 4:2 all correct = 10/10). push-up_52 has TWO people (one stops at ~7 s);
  num_poses=1 tracking jumps between them → 14 vs 25; excluded as out of scope (single-user
  app). Total 40/40 on 9 single-person videos. Committed (13b772c).
  Curl test: user counts 23:1, 53:3, 18:1, 7:2, 52:4; elbow angle 50/150 counted 0 everywhere
  (front view → MediaPipe 3D elbow only reaches 80–95°). Switched curls to
  features.wrist_height (2D: 0 = hips, 1 = shoulders, avg visibility of 6 points), thresholds
  0.3/0.6, counted when bar reaches the top, auto_start (first value sets stage). EXERCISES
  keys now signal/joint/down/up(/auto_start); make_counter(); counter_demo.measure().
  Headless check with real pipeline: curls 11/11, push-ups still 40/40. 22 tests pass.
  Validated by user on new curls 11:1, 50:2, 5:2, 37:1, 17:1 → 7/7. Curls total 18/18.
  Committed (c0b765b).
  Speed: `src/benchmark_speed.py` (default push-up_54, 720p): pose 33.5 ms, LSTM 2.6 ms,
  RF 28 ms (n_jobs=1), counting 0.2 ms → 36 ms/frame ≈ 28 fps, meets <100 ms.
  Fixed: classes were saved as np.str_ → torch.load(weights_only) failed; load_sequences now
  returns plain str; added train_lstm.load_lstm(). I replaced models/exercise_classifier_lstm.pt
  with an identical retrain (same loss). Committed (65fdbfc).
  `src/predict.py VIDEO`: one MediaPipe pass (keypoints + every exercise's measure), LSTM
  votes over 30-frame windows (same preprocessing as training), counts reps for the winner.
  On the 19 counted push-up/curl videos: exercise 19/19, reps 19/19 videos (final model saw
  these videos in training, so classification is optimistic). Not committed.
  PROBLEM: squat counter (knee 100/160) gives 0 reps on dataset squats: standing knee angle
  often only 140–155, and knee visible in only 11–54% of frames in some (squat_3 11%).
  Only validated live on the user before. User counts (after re-count of a mix-up):
  8:1, 9:1, 20:2, 21:2 (tuning) and 3:1, 11:1, 4:4, 6:4, 7:1 (new). Changed squat to 100/140
  → 13/13 reps on 8 videos. squat_4: someone walks in front, knees invisible 6–10.5 s, counts
  2 of 4 → excluded like push-up_52 (view blocked), reported as limitation. Committed (f220d1e).
  Rep counter overall: squat 13/13, pushup 40/40, curl 18/18 (single person, clear view).
  `docs/ML_MODEL_DOCS.md` written (data, preprocessing, models, results, counter, speed,
  limitations, reproduce). Committed (127ba7a). README.md rewritten for the real project
  (results, install, usage, structure). Not committed.
  After this, Phase 2A is complete; next is Phase 2B (Flask backend).
  Note: IMAGE-mode detection took ~70 ms/frame (roadmap target <100 ms/frame).
- The user follows the roadmap: only do the current phase, don't build ahead. Roadmap says to use public datasets before recording our own videos.
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
- Phase 2.2 (current, exercise classifier): roadmap (in ~/Downloads) wants 3 exercises, ≥20
  videos each, 30-frame pose sequences, 70/30 split. Kaggle set has no jumping jacks, so user
  chose squat/pushup/curl. `src/copy_dataset.py` copied all of them from the zip: squat 29,
  pushup 56, curl 62 (147 total) in data/raw_videos/. Not committed.
  All 147 extracted to data/poses/<exercise>/ (min 47 frames/video). 14 flagged bad (low
  detection or hip/shoulder/key-joint visibility < 0.5); user confirmed squat_28 (no knees) and
  curl_41 (arms hidden at start) visually. `src/check_quality.py` writes data/poses/quality.csv
  with a `keep` column (kept: squat 26, pushup 55, curl 52). Committed and pushed.
  `src/make_sequences.py` (+ tests/test_sequences.py): kept videos → normalized x,y (66/frame),
  30-frame windows, stride 15, NaN windows skipped → data/sequences.npz (X, y, video, classes).
  Train/test must be split BY VIDEO (windows overlap). Not committed.
  Fixed after first run: normalize_keypoints now uses ONE torso scale per video (90th pct) —
  per-frame scale exploded on front-view push-ups (values up to 146); fill_short_gaps
  interpolates ≤5-frame gaps (push-up_30 had 0 windows). Result: curl 321, pushup 587,
  squat 435 = 1343 sequences, max |value| 4.5. Committed (2e215fc). data/*.npz now git-ignored.
  Step 6a: `src/train_classifier.py` baseline Random Forest on mean/std/min/max per value
  (264 features), StratifiedGroupKFold(3) by video; split 1 = 88 train / 45 test videos.
  My test run: 98.4% test acc (curl recall 0.95, 4 curls→squat); 3 splits 98.4/98.4/91.3
  (mean 96.1). Saves models/exercise_classifier_rf.joblib. Committed (b3466db). Errors are
  mostly curl<->squat (both standing), spread over videos; split 3 has only 18 train squats.
  Per-video voting would fix almost all → idea for live demo.
  Step 6b: torch 2.14.1+cpu installed (no NVIDIA GPU), requirements.txt updated.
  `src/train_lstm.py`: LSTM64→Dropout→Dense32→3, 40 epochs, Adam, class weights, same splits.
  My run (~30 s): split 1 98.4% (7 squat→curl), splits 98.4/99.1/92.2 (mean 96.6) ≈ baseline.
  Saves models/exercise_classifier_lstm.pt. Not run by user, not committed.
- Later (Phase 2.2+): build the exercise classifier (collect labeled videos,
  extract poses to `data/poses`, features, train in `notebooks/`, save to `models/`).
- Decisions 2026-10-13: 26 squats OK; PyTorch; "mobile inference" = fast server-side inference
  (done, 36 ms); backend goes in THIS repo as `backend/` next to `src/`. Training notebook
  `notebooks/04_classifier_training.ipynb` (reuses src functions; executed, outputs saved;
  same numbers as scripts) closes 2A. train_model has verbose= and model.loss_history. Not
  committed (with README). PHASE 2A DONE. Next: Phase 2B step 1, minimal Flask app in backend/.
- Phase 2B step 1: backend/ (app.py create_app factory, config.py Config/TestConfig,
  routes/health.py GET /api/health -> {"status": "ok"}), tests/test_backend.py, flask added to
  requirements.txt. Run: `python -m backend.app`. Flask not yet installed by user; not committed.

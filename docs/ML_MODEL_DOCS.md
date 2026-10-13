# ML Model Documentation: Exercise Classifier and Rep Counter

Phase 2A of the Personal Trainer AI project. Given a video of one person exercising, the
system recognizes the exercise (squat, push-up or biceps curl) and counts the repetitions.

```
video ─► pose detection ─► normalize ─► 30-frame sequences ─► LSTM ─► vote ─► exercise
          (MediaPipe)        keypoints                                            │
             │                                                                    ▼
             └──────────► joint angle / wrist height per frame ─────────► rep counter ─► reps
```

## 1. Data

**Source:** Kaggle "Workout/Exercises Video" (hasyimabdillah): 652 videos of 22 exercises,
mixed sources (gym videos, tutorials), mixed resolution (720p/1080p), 24–30 fps.

The roadmap planned burpees as the third exercise; the dataset has none, so biceps curls
were used instead.

| Exercise | Videos in dataset | Kept after quality check | 30-frame sequences |
|---|---|---|---|
| Squat | 29 | 26 | 435 |
| Push-up | 56 | 55 | 587 |
| Barbell biceps curl | 62 | 52 | 321 |
| **Total** | **147** | **133** | **1,343** |

**Quality check** (`src/check_quality.py`): a video is kept only if a person is detected in
≥ 80% of frames and the hips, shoulders and the exercise's key joint (knee or elbow) have a
mean visibility ≥ 0.5. A high detection rate alone was not enough: in some videos the person
is "detected" while the knees or arms are out of frame or hidden. 14 videos were removed,
mostly close-up curls and squats with the knees hidden.

## 2. Preprocessing

1. **Pose detection** (`src/extract_poses.py`): MediaPipe Pose Landmarker (full model,
   Tasks API, video mode) gives 33 landmarks per frame with x, y, z and visibility.
2. **Normalization** (`features.normalize_keypoints`): x is corrected for the image aspect
   ratio, every frame is centered on the middle of the hips and divided by the torso length
   (hips to shoulders). The torso length is **one value per video** (its 90th percentile):
   with a per-frame value, push-ups filmed from the front blew up to values of ~150, because
   the torso pointing at the camera looks almost zero long.
3. **Features:** the normalized x and y of the 33 landmarks, 66 numbers per frame. z
   (MediaPipe's depth guess) and visibility are not used.
4. **Gap filling** (`make_sequences.fill_short_gaps`): runs of up to 5 frames without a
   detected person (~0.2 s) are filled by linear interpolation; longer gaps stay missing.
5. **Sequences** (`src/make_sequences.py`): a 30-frame window (~1 s) slides along each
   video in steps of 15 frames. Windows that still contain a missing frame are skipped.

## 3. Exercise classifier

### Models

| | Random Forest (baseline) | **LSTM (used)** |
|---|---|---|
| Script | `src/train_classifier.py` | `src/train_lstm.py` |
| Input | 264 numbers: mean, std, min, max of each feature over the 30 frames | the 30 × 66 sequence, frame by frame |
| Architecture | 300 trees, balanced class weights | LSTM (64) → Dropout (0.5) → Dense (32, ReLU) → 3 classes |
| Training | scikit-learn defaults | Adam, lr 0.001, batch 32, 40 epochs, class-weighted cross-entropy |
| Saved model | `models/exercise_classifier_rf.joblib` | `models/exercise_classifier_lstm.pt` (PyTorch) |

The roadmap planned TensorFlow/Keras (`.h5`); PyTorch was used instead (CPU build).

### Evaluation method

Train and test are split **by video**: all sequences of one video are on the same side.
Windows of one video overlap and show the same person and room, so a split by sequence would
test on near-copies of the training data and overstate the accuracy. `StratifiedGroupKFold`
makes 3 splits with the same exercise mix; each split uses about 2/3 of the videos (88) for
training and 1/3 (45) for testing, close to the roadmap's 70/30. Both models use the same
splits and a fixed random seed. The saved models are then retrained on all videos.

### Results

Accuracy on sequences of videos not seen in training:

| | Split 1 | Split 2 | Split 3 | **Mean** |
|---|---|---|---|---|
| Random Forest | 98.4% | 98.4% | 91.3% | **96.1%** |
| LSTM | 98.4% | 99.1% | 92.2% | **96.6%** |

Roadmap target: > 80%.

LSTM, split 1 (448 test sequences from 45 videos):

| true \ predicted | curl | pushup | squat |
|---|---|---|---|
| curl | 107 | 0 | 0 |
| pushup | 0 | 196 | 0 |
| squat | 7 | 0 | 138 |

**Findings**
- The two models are practically equal in accuracy. The LSTM is chosen because it is about
  10× faster (see section 5).
- The main confusion is **squat ↔ curl**: both are standing exercises, and a 1-second
  window of someone standing with a bar between squats looks like a curl.
- Split 3 is the weakest because it trains on the fewest squat videos (18). Squats have the
  fewest videos overall, so more squat data is the clearest way to improve.
- Errors are spread over many videos and are a minority within each video, so voting over
  all windows of a video (as `src/predict.py` does) classified every tested video correctly.

## 4. Rep counter

`src/rep_counter.py`. Each exercise tracks one signal per frame. A rep is counted with two
thresholds (hysteresis), so small wobbles around one threshold are not counted twice.

| Exercise | Signal | Thresholds | A rep is counted when |
|---|---|---|---|
| Squat | knee angle (3D) | 100° / 140° | the knee goes below 100°, then back above 140° (standing up) |
| Push-up | elbow angle (3D) | 110° / 140° | the elbow goes below 110°, then back above 140° (arms straight) |
| Curl | wrist height (2D) | 0.3 / 0.6 | the wrists rise above 0.6 (bar at the top), after being below 0.3 |

- Angles use MediaPipe's 3D world landmarks, on the more visible body side. Frames where the
  joint's visibility is below 0.5 are skipped.
- **Wrist height** (`features.wrist_height`) is 0 with the wrists at hip level and 1 at
  shoulder level, from image y positions only. Curls are filmed from the front, where the
  forearm moves toward the camera and MediaPipe's depth estimate is poor: the elbow angle only
  reached 80–95° instead of ~40°, and the first angle-based curl counter counted 0 of 11
  reps. Wrist height counted all of them.
- Curls start from the first frame's state (`auto_start`), so a video that begins mid-lift
  still counts that lift, like a person would.

### How the thresholds were chosen and tested

For each exercise, reps were counted by eye in 5 videos, the signal was recorded frame by
frame, and the thresholds were chosen to match. Then they were checked on 4–5 **new**
videos that were not used for tuning. The initial thresholds (squat 100/160, push-up 90/150,
curl elbow 50/150) were too strict for dataset videos: most people in them don't bend or
straighten as fully as the textbook movement.

| Exercise | Tuning videos | New test videos | Reps counted correctly |
|---|---|---|---|
| Squat | 4 | 4 | **13 / 13** |
| Push-up | 5 | 4 | **40 / 40** |
| Curl | 5 | 5 | **18 / 18** |

The squat counter was also tested live on a webcam (5 / 5). Roadmap target: > 95%.

## 5. Speed

`src/benchmark_speed.py`, on push-up_54 (1280 × 720) on the development laptop's CPU (no GPU),
median time per frame:

| Step | ms |
|---|---|
| Pose detection (MediaPipe) | 33.5 |
| Classification, LSTM (last 30 frames) | 2.6 |
| Classification, Random Forest | 28.3 |
| Rep counting | 0.2 |
| **Pipeline with LSTM** | **36 ms ≈ 28 frames per second** |

Roadmap target: < 100 ms per frame. Pose detection takes almost all the time.

## 6. Limitations

- **One person only.** MediaPipe tracks a single person (`num_poses=1`). With two people
  in view (push-up_52) it switched between them and counted 14 of 25 reps.
- **The body must stay visible.** In squat_4 another person walked in front of the camera
  for 4 seconds; the 2 squats in that gap were missed (2 of 4 counted). These two videos are
  excluded from the counting results above.
- **Small test sets:** 71 counted reps in short videos (2–26 s). The classification test
  sets are 44–45 videos per split.
- **Three exercises**, mostly gym videos from the front or diagonal. Other camera angles,
  clothing and exercises are untested.
- The final saved classifier was trained on all videos, so any test on dataset videos with
  it is optimistic. The cross-validated 96.6% is the fair estimate.
- Thresholds were tuned on the same dataset type. A person who squats or curls with a very
  short range of motion may not be counted.

## 7. How to reproduce

From the project root, with `.venv` activated:

```powershell
python src/copy_dataset.py                 # copy squat / push-up / curl videos from the zip
python src/extract_poses.py data/raw_videos  # pose detection -> data/poses/<exercise>/*.csv
python src/check_quality.py                # -> data/poses/quality.csv
python src/make_sequences.py               # -> data/sequences.npz
python src/train_classifier.py             # Random Forest baseline
python src/train_lstm.py                   # LSTM (used model)
python src/benchmark_speed.py              # speed per frame
python src/predict.py VIDEO                # exercise + reps for one video
python src/counter_demo.py --exercise squat  # live rep counter on the webcam
python -m pytest                           # 22 tests
```

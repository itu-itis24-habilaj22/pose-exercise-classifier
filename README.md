# Pose-Based Exercise Classifier and Rep Counter

> Graduation project, Istanbul Technical University. Advisor: Prof. Dr. Mehmet Keskinöz.

The machine-learning core of a **Personal Trainer AI**: from a video of one person
exercising, it recognizes the exercise (**squat, push-up, biceps curl**) and counts the
repetitions. A web app (Flask backend, React frontend) will be built on top of it.

```
video ─► pose detection ─► normalized keypoints ─► LSTM (30-frame sequences) ─► exercise
          (MediaPipe)                                                              │
             └──────────► joint angle / wrist height per frame ─► rep counter ◄────┘ ─► reps
```

## Results

| | Result | Roadmap target |
|---|---|---|
| Exercise classification (LSTM, unseen videos, 3 splits by video) | **96.6%** accuracy | > 80% |
| Rep counting (single person, clear view) | squat 13/13, push-up 40/40, curl 18/18 | > 95% |
| Speed (pose + classification + counting, laptop CPU) | **36 ms per frame** (≈ 28 fps) | < 100 ms |

Details (data, methods, evaluation and limitations): [docs/ML_MODEL_DOCS.md](docs/ML_MODEL_DOCS.md).

## Installation

Developed with **Python 3.12** (MediaPipe may not support newer versions).

```powershell
git clone https://github.com/itu-itis24-habilaj22/pose-exercise-classifier.git
cd pose-exercise-classifier
python -m venv .venv
.venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

The MediaPipe model `models/pose_landmarker_full.task` must be downloaded separately
(MediaPipe Pose Landmarker, full).

## Usage

```powershell
python src/predict.py data/raw_videos/squat/squat_6.MOV      # exercise + reps for a video
python src/counter_demo.py --exercise squat                  # live rep counter (webcam)
python src/pose_demo.py                                      # live skeleton (webcam)
python -m pytest                                             # tests
```

To rebuild the dataset and retrain the models, see
[How to reproduce](docs/ML_MODEL_DOCS.md#7-how-to-reproduce).

## Dataset

Kaggle "Workout/Exercises Video" (hasyimabdillah): 147 videos of squats, push-ups and
barbell biceps curls, 133 kept after a pose quality check. Videos and extracted poses are
not committed to the repository (`data/` is git-ignored).

## Project structure

```
src/
  pose_demo.py           live pose detection and skeleton drawing
  counter_demo.py        live rep counter (webcam or video)
  predict.py             full pipeline: video -> exercise + reps
  features.py            joint angles, wrist height, keypoint normalization
  rep_counter.py         rep counting with two thresholds; per-exercise settings
  copy_dataset.py        copy the three exercises from the Kaggle zip
  extract_poses.py       video -> keypoints CSV (one row per frame)
  check_quality.py       per-video detection / visibility check
  make_sequences.py      kept videos -> 30-frame training sequences
  train_classifier.py    Random Forest baseline
  train_lstm.py          LSTM classifier (used model)
  benchmark_speed.py     time per frame of each pipeline step
  explore_videos.py, plot_poses.py, opencv_*_basics.py   exploration and learning scripts
tests/                   unit tests (pytest)
docs/ML_MODEL_DOCS.md    model documentation
models/                  trained models (git-ignored)
data/                    videos, poses, sequences (git-ignored)
```

## References

1. Bazarevsky et al., *BlazePose: On-device Real-time Body Pose Tracking*, 2020.
2. Hochreiter and Schmidhuber, *Long Short-Term Memory*, Neural Computation, 1997.

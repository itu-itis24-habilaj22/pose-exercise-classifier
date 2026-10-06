# Pose-Based Exercise Classifier and Rep Counter

> Graduation project — [Your Name], [University], [Department], [Year]
> Supervisor: [Supervisor Name]

## Overview

This project uses human pose estimation to **recognize which exercise** a person is doing
(e.g. squat, push-up, bicep curl, lunge, jumping jack) from video, and to **count repetitions**
automatically.

**Pipeline:**

```
Video ──► Pose estimation ──► Keypoint features ──► Exercise classifier ──► Rep counter ──► Output
          (MediaPipe)         (joint angles,         (e.g. RF / LSTM)       (angle-based
                               normalized coords)                            state machine)
```

## Goals

- [ ] Extract 2D/3D body keypoints from exercise videos
- [ ] Engineer pose features (joint angles, normalized coordinates, velocities)
- [ ] Train a classifier to identify the exercise type
- [ ] Count repetitions per exercise using joint-angle thresholds / peak detection
- [ ] Run in real time on webcam input
- [ ] Evaluate accuracy (classification) and counting error (MAE)

## Supported Exercises

| Exercise     | Key joint(s) for counting | Status |
|--------------|---------------------------|--------|
| Squat        | Knee angle                | TODO   |
| Push-up      | Elbow angle               | TODO   |
| Bicep curl   | Elbow angle               | TODO   |
| Lunge        | Knee angle                | TODO   |
| Jumping jack | Shoulder / hip angle      | TODO   |

## Project Structure

```
pose-exercise-classifier/
├── data/
│   ├── raw_videos/      # Original exercise videos (not tracked by git)
│   ├── poses/           # Extracted keypoints per video (.csv / .npy)
│   └── processed/       # Feature datasets ready for training
├── models/              # Saved trained models (.pkl / .h5 / .pt)
├── notebooks/           # Jupyter notebooks for exploration and experiments
├── src/
│   ├── extract_poses.py # Video → keypoints
│   ├── features.py      # Keypoints → features (angles, etc.)
│   ├── train.py         # Train the exercise classifier
│   ├── rep_counter.py   # Repetition counting logic
│   └── app.py           # Real-time webcam / video demo
├── tests/               # Unit tests
├── requirements.txt
└── README.md
```

## Installation

Requires **Python 3.10–3.12** (MediaPipe may not yet support newer versions).

```bash
git clone https://github.com/<your-username>/pose-exercise-classifier.git
cd pose-exercise-classifier

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Usage

```bash
# 1. Extract poses from videos
python src/extract_poses.py --input data/raw_videos --output data/poses

# 2. Train the classifier
python src/train.py --data data/processed --output models/

# 3. Run the real-time demo
python src/app.py --model models/classifier.pkl --source 0   # 0 = webcam
```

## Dataset

- **Source:** [e.g. self-recorded / Kaggle / InfiniteRep / Fitness-AQA]
- **Size:** [N videos, M exercises, K subjects]
- **Labels:** exercise class + ground-truth rep count per video

Raw videos are not committed to the repository. Download/placement instructions: [link or notes].

## Methodology

### Pose Estimation
[Describe the pose model, e.g. MediaPipe Pose — 33 landmarks, and why you chose it.]

### Feature Engineering
[Joint angles, normalization by torso length, temporal windows, etc.]

### Classification
[Model(s) tried, window size, train/val/test split strategy (split by subject!).]

### Repetition Counting
[e.g. state machine over joint angle: "up" → "down" → "up" = 1 rep, with hysteresis thresholds.]

## Results

| Model          | Accuracy | F1-score |
|----------------|----------|----------|
| [Model A]      | –        | –        |
| [Model B]      | –        | –        |

| Exercise   | Rep count MAE |
|------------|---------------|
| Squat      | –             |
| Push-up    | –             |

## Demo

[Add a GIF or screenshot here.]

## Future Work

- [Form/posture correction feedback]
- [More exercises]
- [Mobile deployment]

## References

1. Bazarevsky et al., *BlazePose: On-device Real-time Body Pose Tracking*, 2020.
2. [Add more]

## License

[MIT / other — choose one]

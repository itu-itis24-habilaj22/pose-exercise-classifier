# Changelog

The notable changes to this project, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Each release matches a git tag and
a GitHub Release, and the WBS IDs point to [docs/WBS.md](docs/WBS.md).

## [Unreleased]

Phase R: bringing the work of Phases 1 and 2 into a branch and pull request workflow.

### Added
- CI now has three separate checks: `lint` (ruff), `test` (pytest with a 54% coverage
  minimum) and `dependency-scan` (pip-audit). (WBS-R.1, #1)
- `requirements-dev.txt` for development tools, and `pyproject.toml` with the ruff, pytest
  and coverage settings. (WBS-R.1, #1)
- `main` is protected by a ruleset: changes only through pull requests, all three checks must
  pass, no force pushes or deletion. (WBS-R.2)
- Requirement IDs in `docs/REQUIREMENTS.md`, the work breakdown in `docs/WBS.md`, a pull
  request template, `CONTRIBUTING.md` and this changelog. (WBS-R.3, #2)

### Changed
- `requirements.txt` only lists what the app needs to run. pytest, Jupyter, matplotlib and
  seaborn moved to `requirements-dev.txt`. (WBS-R.1, #1)
- The CI workflow file was renamed from `tests.yml` to `ci.yml`. (WBS-R.1, #1)
- The repository is now public. (WBS-R.2)
- Test files are named by requirement ID, for example `test_auth.py` is now
  `test_fr06_auth.py`. The tests themselves did not change. (WBS-R.4)

### Fixed
- Five issues reported by ruff: import order, an unused import in the training notebook and
  two lines over 100 characters. (WBS-R.1, #1)

## [0.2.0-baseline] - 2026-11-24

The state of the project at the end of Phase 2 (work done from Oct 6 to Oct 15, 2026),
before the workflow rework. Everything up to here was committed straight to `main`.

### Added
- Pose detection on webcam and video with MediaPipe, keypoint extraction and normalization.
  (WBS-1.1 to 1.5)
- Dataset preparation from the Kaggle "Workout/Exercises Video" set: squats, push-ups and
  bicep curls, filtered by pose quality, cut into 30-frame sequences. (WBS-2.2, 2.3)
- Exercise classifier: Random Forest baseline and an LSTM in PyTorch, 96.6% accuracy on
  unseen videos. (WBS-2.4)
- Rep counter for all three exercises, 71 of 71 reps on the test videos. (WBS-2.1)
- Prediction script, speed benchmark (36 ms per frame), ML documentation and training
  notebook. (WBS-2.5, 2.6)
- Flask backend with PostgreSQL: health check, signup and login with JWT, workouts, history,
  stats, premium progress and the live detection API. (WBS-2.7 to 2.12)
- API documentation, Postman collection, and tests on GitHub Actions. (WBS-2.13, 2.14)

[Unreleased]: https://github.com/itu-itis24-habilaj22/pose-exercise-classifier/compare/v0.2.0-baseline...HEAD
[0.2.0-baseline]: https://github.com/itu-itis24-habilaj22/pose-exercise-classifier/releases/tag/v0.2.0-baseline

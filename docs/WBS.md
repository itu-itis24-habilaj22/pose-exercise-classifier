# Work breakdown structure (WBS)

This is the list of all work in the project, split into activities. Each activity has an ID
(`WBS-<phase>.<activity>`), and from Phase R on each one gets its own branch and pull request.
The requirement IDs (FR, NFR) are explained in [REQUIREMENTS.md](REQUIREMENTS.md).

Phases 1 and 2 were done before I used branches, pull requests or WBS IDs; everything was
committed straight to `main`. I gave those activities IDs afterwards and linked each one to
the commits that did the work, so the whole project can be followed in one place. That state
is frozen in the tag `v0.2.0-baseline`.

## Phase 1: Pose pipeline (Oct 6 to Oct 7, 2026)

| WBS | Activity | Requirements | Commits | Status |
|---|---|---|---|---|
| 1.1 | Project setup: git, GitHub repo, Python 3.12 venv, requirements, folder structure | | `d22cf58` | Done |
| 1.2 | Pose detection demo on webcam and video files (MediaPipe Tasks API) | FR-01 | `a3cc26c` | Done |
| 1.3 | OpenCV basics for images and video (learning scripts) | | `432c640` | Done |
| 1.4 | Extract pose keypoints to CSV, normalize them, plot them | FR-01 | `c571f5e` | Done |
| 1.5 | Choose a public dataset, explore sample videos, batch pose extraction | FR-01 | `e3db28b` | Done |

## Phase 2: Machine learning and backend (Oct 6 to Oct 15, 2026)

Phase 2A, machine learning:

| WBS | Activity | Requirements | Commits | Status |
|---|---|---|---|---|
| 2.1 | Joint angles and rep counter: live squat test, push-up thresholds, curls by wrist height, squat thresholds | FR-03, NFR-02 | `4901a6c`, `13b772c`, `c0b765b`, `f220d1e` | Done |
| 2.2 | Copy the full dataset for 3 exercises and filter videos by pose quality | FR-01 | `e727411` | Done |
| 2.3 | 30-frame pose sequences with per-video scale and gap filling | FR-02 | `2e215fc` | Done |
| 2.4 | Exercise classifier: Random Forest baseline, then LSTM, split by video | FR-02, FR-04, NFR-01 | `b3466db`, `58edab8` | Done |
| 2.5 | Speed benchmark and prediction script (classify and count one video) | FR-04, NFR-03 | `65fdbfc`, `f220d1e` | Done |
| 2.6 | ML documentation and training notebook | NFR-01 to NFR-03 | `127ba7a`, `953f42c` | Done |

Phase 2B, backend:

| WBS | Activity | Requirements | Commits | Status |
|---|---|---|---|---|
| 2.7 | Minimal Flask app with health endpoint | FR-05 | `8864b65` | Done |
| 2.8 | PostgreSQL connection and database models with seed data | FR-05, FR-07 | `d16afa4`, `745fac1` | Done |
| 2.9 | Signup, login and token auth (bcrypt, JWT) | FR-06, NFR-04 | `c1b8d86` | Done |
| 2.10 | Workout CRUD API and public exercise list | FR-08 | `ce7eb18` | Done |
| 2.11 | Exercise history, stats and premium progress API | FR-09 | `c8358cc` | Done |
| 2.12 | Live detection API (sessions, frames, summary) | FR-10, FR-03, FR-04 | `aa3e6b3` | Done |
| 2.13 | API documentation, Postman collection, CORS | FR-05 to FR-10 | `f021243`, `56d91b5` | Done |
| 2.14 | Run the tests on GitHub Actions | | `049a89f`, `b515255` | Done |

## Phase R: Bring Phases 1 and 2 into the workflow (Nov 24 to Dec 27, 2026)

| WBS | Dates | Branch | Activity | Status |
|---|---|---|---|---|
| R.0 | Nov 24 | none | Tag `v0.2.0-baseline` and GitHub Release | Done |
| R.1 | Nov 24 | `ci/wbs-r.1-ci-gates` | CI split into lint, test (coverage gate) and dependency-scan; dev requirements; ruff fixes | Done (PR #1) |
| R.2 | Nov 24 | none | Repo made public; ruleset protects `main` (PR required, 3 checks, no force push) | Done |
| R.3 | Nov 24 to Dec 6 | `docs/wbs-r.3-requirements-wbs` | Requirements, WBS, PR template, contributing guide, changelog | In progress |
| R.4 | Dec 7 to Dec 13 | `test/wbs-r.4-tests-by-requirement` | Rename test files with requirement IDs | Planned |
| R.5 | Dec 14 to Dec 20 | `test/wbs-r.5-ml-tests-in-ci` | Run the detection tests in CI, add a classifier test, raise the coverage gate | Planned |
| R.6 | Dec 21 to Dec 24 | `chore/wbs-r.6-cleanup` | Move learning scripts out of `src/`, pin versions, trim the progress log | Planned |
| R.7 | Dec 27 | none | Tag and release `v0.2.1` | Planned |

## Phase 3: Frontend and integration (Jan 4 to Feb 28, 2027)

| WBS | Dates | Branch | Activity | Requirements | Status |
|---|---|---|---|---|---|
| 3.1 | Jan 4 to Jan 8 | `feat/wbs-3.1-react-setup` | Vite + React app, routing, API client, ESLint, Vitest, frontend CI job | | Planned |
| 3.2 | Jan 9 to Jan 15 | `feat/wbs-3.2-auth-pages` | Login and signup pages, token storage, protected routes | FR-11 | Planned |
| 3.3 | Jan 16 to Jan 22 | `feat/wbs-3.3-dashboard` | Dashboard with stats | FR-12 | Planned |
| 3.4 | Jan 23 to Jan 31 | `feat/wbs-3.4-workout-planner` | Create, edit and delete workouts | FR-13 | Planned |
| 3.5a | Feb 1 to Feb 8 | `feat/wbs-3.5a-camera-capture` | Camera page that sends frames to the detection API | FR-14 | Planned |
| 3.5b | Feb 9 to Feb 15 | `feat/wbs-3.5b-rep-feedback` | Live rep counter, detected exercise, feedback; save the set | FR-14 | Planned |
| 3.6 | Feb 16 to Feb 20 | `feat/wbs-3.6-history-charts` | History list and progress charts | FR-15 | Planned |
| 3.7 | Feb 21 to Feb 27 | `test/wbs-3.7-e2e-responsive` | Responsive layout and one end-to-end test | NFR-06 | Planned |
| 3.R | Feb 28 | none | Tag and release `v0.3.0` | | Planned |

## Phase 4: Polish, deployment, documentation (Mar 1 to Jun 15, 2027)

| WBS | Dates | Branch | Activity | Requirements | Status |
|---|---|---|---|---|---|
| 4.1 | Mar 1 to Mar 20 | `feat/wbs-4.1-form-guidance` | Demonstration videos, form guidance and form score | FR-16 | Planned |
| 4.2 | Mar 21 to Mar 31 | `chore/wbs-4.2-deploy-prep` | Hosting choice, Dockerfile, gunicorn, Flask-Migrate | | Planned |
| 4.3 | Apr 1 to Apr 30 | `ci/wbs-4.3-deploy` | HTTPS deployment, deploy workflow on `v*` tags | NFR-05 | Planned |
| 4.R1 | Apr 30 | none | Tag and release `v0.4.0` (first deployed version) | | Planned |
| 4.4 | May 1 to May 20 | `test/wbs-4.4-device-testing` | Phone and camera test matrix, fixes with regression tests | NFR-06 | Planned |
| 4.5 | May 21 to May 31 | `perf/wbs-4.5-performance` | Performance tuning and a speed test | NFR-03 | Planned |
| 4.6 | Jun 1 to Jun 10 | `docs/wbs-4.6-final-docs` | Technical docs, diagrams, setup guide, final test report | | Planned |
| 4.R2 | Jun 10 | none | Tag and release `v1.0.0` | | Planned |
| 4.7 | Jun 11 to Jun 15 | none | Final presentation and written report | | Planned |

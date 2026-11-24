# Requirements

This file lists what the project has to do (functional requirements, FR) and how well it has
to do it (non-functional requirements, NFR). Every requirement has a fixed ID. Branches, pull
requests and test files refer to these IDs, so once an ID is used it keeps its number, even if
the wording changes later.

The requirements come from the project roadmap. Phases 1 and 2 were built before I started
using IDs, so for those I matched the existing tests to the requirements afterwards.

## Functional requirements

| ID | Requirement | Phase | Status |
|---|---|---|---|
| FR-01 | Extract pose keypoints from a video or webcam and normalize them (hip-centered, torso-scaled) | 1 | Done |
| FR-02 | Build 30-frame pose sequences for training, and split train/test by video | 1–2 | Done |
| FR-03 | Count repetitions for squats, push-ups and bicep curls | 2 | Done |
| FR-04 | Recognize which exercise is being done from a pose sequence | 2 | Done |
| FR-05 | API health endpoint that reports the status of the API and the database | 2 | Done |
| FR-06 | Sign up, log in, and protect endpoints with a login token; premium-only endpoints | 2 | Done |
| FR-07 | Store users, exercises, workouts and exercise history in the database | 2 | Done |
| FR-08 | Create, read, update and delete workout plans | 2 | Done |
| FR-09 | Save finished sets to history; show stats and progress over time | 2 | Done |
| FR-10 | Live detection API: start a session, send camera frames, get the exercise and rep count, end with a summary | 2 | Done |
| FR-11 | Login and signup pages in the web app | 3 | Planned |
| FR-12 | Dashboard with the user's stats | 3 | Planned |
| FR-13 | Workout planner page (create, edit, delete) | 3 | Planned |
| FR-14 | Camera page with live rep counting, detected exercise and feedback; save the set to history | 3 | Planned |
| FR-15 | History list and progress charts | 3 | Planned |
| FR-16 | Form guidance and exercise demonstration videos, including a form score | 4 | Planned |

## Non-functional requirements

| ID | Requirement | Phase | Status |
|---|---|---|---|
| NFR-01 | Exercise classification above 80% accuracy on videos the model has not seen | 2 | Met: 96.6% (LSTM, mean of 3 splits by video) |
| NFR-02 | Rep counting above 95% correct | 2 | Met: 71 of 71 reps (one person, clear view) |
| NFR-03 | Under 100 ms per frame for pose detection, classification and counting together | 2, 4 | Met: 36 ms on a laptop CPU |
| NFR-04 | Passwords stored only as bcrypt hashes; no secrets in the repository | 2 | Met |
| NFR-05 | Served over HTTPS, so phone browsers allow camera access | 4 | Planned |
| NFR-06 | Usable on desktop and phone browsers | 3–4 | Planned |
| NFR-07 | Test coverage of at least 80% for the backend and the ML modules | R | In progress: 54% in CI (gate in `ci.yml`) |

The numbers for NFR-01 to NFR-03 and how they were measured are in
[ML_MODEL_DOCS.md](ML_MODEL_DOCS.md).

## Which tests cover which requirement

Test counts are what pytest collects (parametrized tests count once per case), 74 in total.
The detection tests need the trained model and the dataset videos, which are not in the
repository, so they are skipped on GitHub. WBS-R.5 will make them run in CI.

| ID | Test file | Tests | What they check |
|---|---|---|---|
| FR-01 | `tests/test_normalize.py` | 4 | Hips at the origin and torso as one unit, same pose anywhere in the image gives the same result, one scale per video, missing frames stay missing |
| FR-02 | `tests/test_sequences.py` | 5 | Window count and shape, short gaps filled, long gaps left missing, windows with missing frames skipped, video shorter than one window |
| FR-03 | `tests/test_rep_counting.py` | 13 | Joint angles (2D and 3D), wrist height, full reps counted, half reps not counted, wobble at the bottom counts once, auto start for curls, a working counter for every exercise |
| FR-03, FR-04, FR-10 | `tests/test_detect.py` | 8 | Detection needs login, bad input rejected, sessions are private, summary at the end; one push-up, one curl and one squat video streamed frame by frame must give the right exercise and rep count (skipped in CI) |
| FR-05 | `tests/test_backend.py` | 3 | Health endpoint, unknown URL gives 404, CORS only allows the React dev server |
| FR-06, NFR-04 | `tests/test_auth.py` | 9 | Signup and login, password stored hashed, bad data and duplicates rejected, invalid, foreign and expired tokens rejected, premium-only access |
| FR-07 | `tests/test_models.py` | 6 | New users are free tier, unique emails, workouts and history belong to a user and are deleted with them, the 3 exercises are seeded once |
| FR-08 | `tests/test_workouts.py` | 11 | Create, list, get, update and delete; validation; login needed; users can't see or change each other's workouts; public exercise list |
| FR-09 | `tests/test_history.py` | 15 | Save and list history, filters, validation, stats (also for a new user), progress per day for premium users only, users only see their own history |

### Known gaps

- FR-02: the split by video is done in `train_classifier.split_by_video`, which has no unit
  test yet.
- FR-04: the classifier is only tested through `test_detect.py`, so CI never checks it. A
  separate classifier test is planned in WBS-R.5.
- NFR-01 to NFR-03 are measured by scripts (`train_lstm.py`, `predict.py`,
  `benchmark_speed.py`), not by automated tests. NFR-03 becomes a test in WBS-4.5.
- NFR-04 "no secrets in the repository" is kept by `.gitignore` (`.env` is never committed),
  not by a test.

In WBS-R.4 the test files get renamed with their requirement ID (for example
`test_auth.py` becomes `test_fr06_auth.py`), and this table will be updated.

# API Documentation

REST API of the Personal Trainer AI backend (Flask, Phase 2B). All requests and responses use
JSON, except camera frames (form-data). A Postman collection with every request is in
[postman_collection.json](postman_collection.json).

**Base URL (local):** `http://127.0.0.1:5000`. Start the server with `python -m backend.app`
(setup: README and `.env.example`).

## Authentication

Sign up or log in to get a **token** (JWT, valid 7 days). Send it with every request marked 🔒:

```
Authorization: Bearer <token>
```

Endpoints marked 💎 also need a premium subscription.

## Errors

Errors return a JSON body `{"error": "message for the user"}` with one of these status codes:

| Code | Meaning |
|---|---|
| 400 | The data sent is invalid (the message says what is wrong) |
| 401 | Missing, invalid or expired token; or wrong email/password at login |
| 403 | Premium subscription required |
| 404 | Not found, or it belongs to another user |
| 409 | Email or username already taken |
| 413 | Request too large (frames: max 2 MB) |
| 503 | Database unreachable (health), or too many detection sessions open |

---

## Health

### `GET /api/health`
Checks that the server and the database work.
```json
200 {"status": "ok", "database": "ok"}
503 {"status": "degraded", "database": "error: OperationalError"}
```

## Auth

### `POST /api/auth/signup`
```json
{"username": "faby", "email": "faby@example.com", "password": "at-least-8-chars"}
```
Username 3–50 characters; password 8–72 bytes; email stored in lower case.
```json
201 {"user": {"user_id": 1, "username": "faby", "email": "faby@example.com",
              "subscription_tier": "free", "created_at": "2026-11-03T10:00:00+00:00"},
     "token": "eyJhbGciOi..."}
```
Errors: 400 invalid data, 409 email or username taken.

### `POST /api/auth/login`
```json
{"email": "faby@example.com", "password": "at-least-8-chars"}
```
`200 {"user": {...}, "token": "..."}`. Wrong email or password: 401 with the same message for
both, so the API doesn't reveal which emails have an account.

### `GET /api/auth/me` 🔒
`200 {"user": {...}}`: the logged-in user.

## Exercises

### `GET /api/exercises`
Public. The supported exercises.
```json
200 {"exercises": [{"exercise_id": 1, "name": "pushup", "display_name": "Push-up",
                    "instructions": "...", "target_reps": 10, "difficulty": "intermediate",
                    "demo_video_url": null}, ...]}
```
`name` (`pushup`, `squat`, `curl`) is the value used everywhere else in the API.

## Workouts 🔒

A user's workout plans. A user only sees their own; another user's workout id gives 404.

### `GET /api/workouts`
`200 {"workouts": [workout, ...]}`, oldest first.

### `POST /api/workouts`
```json
{"name": "Monday Push Day",
 "exercises": [{"exercise": "pushup", "sets": 3, "target_reps": 10},
               {"exercise": "curl", "sets": 3, "target_reps": 12}]}
```
Name 1–100 characters; 1–20 exercises; sets 1–20 and target_reps 1–200 (whole numbers).
```json
201 {"workout": {"workout_id": 1, "name": "Monday Push Day", "exercises": [...],
                 "created_at": "...", "updated_at": "..."}}
```

### `GET /api/workouts/<workout_id>`
`200 {"workout": {...}}`

### `PUT /api/workouts/<workout_id>`
Same body as POST; replaces the name and the exercises. `200 {"workout": {...}}`

### `DELETE /api/workouts/<workout_id>`
`204` (no body).

## History and statistics 🔒

### `POST /api/history`
Saves one finished exercise (one set), usually the summary of a detection session.
```json
{"exercise": "squat", "reps_completed": 12, "duration": 45,
 "form_score": 88, "voice_enabled": false}
```
reps_completed 0–1000; duration in seconds, 1–14400; form_score 0–100 or left out;
voice_enabled true/false (default false). The date is set by the server.
```json
201 {"entry": {"history_id": 1, "exercise": "squat", "reps_completed": 12, "duration": 45,
               "form_score": 88.0, "voice_enabled": false, "date_completed": "..."}}
```

### `GET /api/history`
Newest first. Optional filters: `?exercise=squat`, `?from=2026-11-01`, `?to=2026-11-30`
(dates in UTC). `200 {"history": [entry, ...]}`

### `GET /api/stats`
Basic statistics (free and premium).
```json
200 {"stats": {"total_sessions": 3, "total_reps": 45, "total_duration": 180,
               "reps_this_week": 25, "average_form_score": 85.0,
               "per_exercise": {"squat": {"sessions": 2, "total_reps": 25, "best_set": 15}}}}
```
`reps_this_week` covers the last 7 days. `average_form_score` is null when no entry has one.

### `GET /api/progress` 💎
Reps per day for the charts. `?days=30` (1–365, default 30), ending today (UTC).
```json
200 {"progress": {"days": ["2026-11-01", ..., "2026-11-30"],
                  "reps": {"pushup": [0, 15, ...], "squat": [...], "curl": [...]}}}
```

## Live detection 🔒

Recognizes the exercise and counts reps from camera frames. The flow for one set:

1. `POST /api/detect/sessions`: start; get a `session_id`.
2. `POST /api/detect/sessions/<session_id>/frames` for every camera frame (about 10–30 per
   second); each answer has the current exercise, rep count and skeleton points.
3. `DELETE /api/detect/sessions/<session_id>`: end; get the summary, then save it with
   `POST /api/history`.

Sessions belong to the user who started them and close after 10 minutes without frames.

### `POST /api/detect/sessions`
```json
{"exercise": "pushup"}
```
`exercise` is optional: the exercise the user picked (e.g. from their workout); reps are
counted for it. Without it, reps are counted for the exercise the classifier recognizes.
```json
201 {"session_id": "3f2a9c...", "exercise": "pushup"}
```
Errors: 400 unknown exercise; 503 too many sessions open on the server.

### `POST /api/detect/sessions/<session_id>/frames`
Body: **form-data** with one field `frame` = a JPEG or PNG image (max 2 MB; 640×480 is enough).
```json
200 {"result": {"frame": 87, "person_detected": true,
                "detected_exercise": "pushup", "confidence": 1.0,
                "counted_exercise": "pushup", "reps": 2, "form_score": null,
                "landmarks": [[0.512, 0.318, 0.998], ...]}}
```
- `detected_exercise`: the classifier's answer (a vote over its last 5 predictions, made every
  15 frames); null during the first ~30 frames with a person in view. `confidence`: the share
  of those votes.
- `counted_exercise`: the exercise whose reps are counted (the chosen one, else the detected one).
- `landmarks`: the 33 MediaPipe body points as `[x, y, visibility]`, x and y as fractions of
  the image width and height (0–1), for drawing the skeleton; null when no person is found.
- `form_score`: null until form feedback (Phase 4).

Errors: 400 missing or invalid image; 404 session not found or expired.

### `DELETE /api/detect/sessions/<session_id>`
```json
200 {"summary": {"exercise": "pushup", "reps": 12, "frames": 640, "duration": 38}}
```
`duration` in seconds.

## Notes for deployment

- Detection sessions live in the server process's memory: run **one** server process with
  several threads (e.g. `gunicorn -w 1 --threads 8`), or sessions won't be found.
- Set `SECRET_KEY`, `DATABASE_URL` and `CORS_ORIGINS` (the website's address) on the host.

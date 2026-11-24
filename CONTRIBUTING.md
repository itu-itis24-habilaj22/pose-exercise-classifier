# How work is done in this repository

This is a one-person graduation project, but I follow the same workflow a team would. All
work is planned as activities in [docs/WBS.md](docs/WBS.md), and every change reaches `main`
through a pull request with green CI. `main` is protected, so direct pushes are rejected,
including mine.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-dev.txt
```

`requirements.txt` has only what the app needs to run. `requirements-dev.txt` adds the
tools for testing, linting and the notebooks.

## The loop for every activity

```powershell
git switch main
git pull
git switch -c <type>/wbs-<id>-<short-name>
# work, commit, repeat
git push -u origin <branch>
```

Then open a pull request on GitHub, wait for the checks, read the whole diff, and merge with
**Squash and merge**. Delete the branch on GitHub and locally:

```powershell
git switch main
git pull
git fetch --prune
git branch -D <branch>   # -D because git does not recognize squashed branches as merged
```

## Naming

- **Branches:** `<type>/wbs-<id>-<short-name>`, lowercase. Types: `feat`, `fix`, `test`,
  `ci`, `docs`, `chore`, `perf`. Example: `feat/wbs-3.2-auth-pages`.
- **Commits:** start with the WBS ID and use the imperative, for example
  `WBS-3.2: Add login form validation`. Small commits are fine; they get squashed.
- **Pull requests:** title `WBS-<id>: <summary>`, for example `WBS-3.2: Login and signup
  pages`. The description follows the template that GitHub fills in.
- **Tests:** the file name carries the requirement ID, for example `tests/test_fr06_auth.py`
  or `frontend/src/__tests__/FR-11-login.test.jsx`.

## Checks before merging

Three checks run on every pull request and all three must pass:

| Check | What it runs |
|---|---|
| `lint` | `ruff check .` (settings in `pyproject.toml`) |
| `test` | `python -m pytest --cov` with a minimum coverage (`--cov-fail-under` in `.github/workflows/ci.yml`) |
| `dependency-scan` | `pip-audit` on the runtime packages |

To run the same things locally:

```powershell
ruff check .
python -m pytest --cov --cov-report=term-missing
pip-audit
```

The detection tests in `tests/test_detect.py` need the trained model and the dataset videos.
They are skipped when those files are missing, which is the case on GitHub for now.

## Review

There is no second reviewer, so I review my own pull requests: I read the "Files changed"
tab from top to bottom before merging and leave a comment on anything I'm unsure about. The
branch also has to be up to date with `main`.

## Bugs

A bug found later gets its own branch, for example `fix/wbs-3.4-planner-delete-crash`,
with a test that fails before the fix and passes after it.

## Releases

At the end of each phase I tag `main` with an annotated tag and publish a GitHub Release,
and move the entries under "Unreleased" in [CHANGELOG.md](CHANGELOG.md) to that version.
Versions are listed in [docs/WBS.md](docs/WBS.md).

## Data and secrets

Never commit the dataset videos, extracted poses, trained models or `.env`. They are in
`.gitignore`. Settings like the database password and `SECRET_KEY` live in `.env` locally
(see `.env.example`) and in GitHub Actions secrets for deployment.

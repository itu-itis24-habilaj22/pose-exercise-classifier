"""Signup, login and "who am I".

POST /api/auth/signup  {"username", "email", "password"}  -> 201 {"user", "token"}
POST /api/auth/login   {"email", "password"}              -> 200 {"user", "token"}
GET  /api/auth/me      (needs the token)                  -> 200 {"user"}
"""
from flask import Blueprint, g, jsonify, request

from backend.auth import check_password, create_token, hash_password, login_required
from backend.db import db
from backend.models import User

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72  # bcrypt only uses the first 72 bytes


def signup_errors(username, email, password):
    """Problems with the signup data, as a list of messages (empty if all is fine)."""
    errors = []
    if not 3 <= len(username) <= 50:
        errors.append("Username must be 3 to 50 characters.")
    if "@" not in email or "." not in email.split("@")[-1] or len(email) > 255:
        errors.append("Email address is not valid.")
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if len(password.encode()) > MAX_PASSWORD_BYTES:
        errors.append(f"Password must be at most {MAX_PASSWORD_BYTES} bytes.")
    return errors


@bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    errors = signup_errors(username, email, password)
    if errors:
        return jsonify(error=" ".join(errors)), 400
    if db.session.scalar(db.select(User).filter_by(email=email)):
        return jsonify(error="An account with this email already exists."), 409
    if db.session.scalar(db.select(User).filter_by(username=username)):
        return jsonify(error="This username is taken."), 409

    user = User(username=username, email=email, password_hash=hash_password(password))
    db.session.add(user)
    db.session.commit()
    return jsonify(user=user.to_dict(), token=create_token(user)), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    user = db.session.scalar(db.select(User).filter_by(email=email))
    # Same message whether the email or the password is wrong, so the API doesn't
    # reveal which emails have an account.
    if user is None or len(password.encode()) > MAX_PASSWORD_BYTES \
            or not check_password(password, user.password_hash):
        return jsonify(error="Wrong email or password."), 401
    return jsonify(user=user.to_dict(), token=create_token(user))


@bp.get("/me")
@login_required
def me():
    return jsonify(user=g.user.to_dict())

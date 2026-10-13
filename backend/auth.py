"""Password hashing, login tokens (JWT) and the decorators that protect endpoints.

Protect an endpoint by putting @login_required (or @premium_required) under the route;
inside it, g.user is the logged-in User.
"""
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import current_app, g, jsonify, request

from backend.db import db
from backend.models import User

TOKEN_ALGORITHM = "HS256"


def hash_password(password):
    rounds = current_app.config["BCRYPT_ROUNDS"]
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds)).decode()


def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.user_id),  # who the token belongs to
        "iat": now,                # issued at
        "exp": now + timedelta(days=current_app.config["TOKEN_DAYS"]),  # expires
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm=TOKEN_ALGORITHM)


def user_from_request():
    """The User whose valid token is in the Authorization header, or None."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(header.removeprefix("Bearer "), current_app.config["SECRET_KEY"],
                             algorithms=[TOKEN_ALGORITHM])
    except jwt.InvalidTokenError:  # bad signature, expired, malformed...
        return None
    return db.session.get(User, int(payload["sub"]))


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = user_from_request()
        if user is None:
            return jsonify(error="Login required"), 401
        g.user = user
        return view(*args, **kwargs)
    return wrapper


def premium_required(view):
    """Like login_required, and the user must have the premium tier."""
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if g.user.subscription_tier != "premium":
            return jsonify(error="Premium subscription required"), 403
        return view(*args, **kwargs)
    return wrapper

from backend.db import db
from backend.models import User

GOOD = {"username": "faby", "email": "Faby@Example.com", "password": "correct-horse"}


def signup(client, **changes):
    return client.post("/api/auth/signup", json={**GOOD, **changes})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_signup_returns_user_and_token(client):
    response = signup(client)
    assert response.status_code == 201
    body = response.get_json()
    assert body["user"]["username"] == "faby"
    assert body["user"]["email"] == "faby@example.com"  # stored in lower case
    assert body["user"]["subscription_tier"] == "free"
    assert "password_hash" not in body["user"]
    assert body["token"]


def test_password_is_stored_hashed(client):
    signup(client)
    user = db.session.scalar(db.select(User))
    assert user.password_hash != GOOD["password"]
    assert user.password_hash.startswith("$2")  # bcrypt format


def test_signup_rejects_bad_data(client):
    assert signup(client, password="short").status_code == 400
    assert signup(client, email="not-an-email").status_code == 400
    assert signup(client, username="ab").status_code == 400
    assert client.post("/api/auth/signup", data="not json").status_code == 400


def test_signup_duplicate_email_or_username(client):
    signup(client)
    assert signup(client, username="other").status_code == 409             # same email
    assert signup(client, email="other@example.com").status_code == 409    # same username


def test_login_with_right_and_wrong_password(client):
    signup(client)
    ok = client.post("/api/auth/login", json={"email": "faby@example.com",
                                              "password": GOOD["password"]})
    assert ok.status_code == 200 and ok.get_json()["token"]
    wrong = client.post("/api/auth/login", json={"email": "faby@example.com",
                                                 "password": "wrong-password"})
    assert wrong.status_code == 401
    unknown = client.post("/api/auth/login", json={"email": "nobody@example.com",
                                                   "password": GOOD["password"]})
    assert unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json()  # doesn't reveal which one was wrong


def test_me_needs_a_valid_token(client):
    token = signup(client).get_json()["token"]
    me = client.get("/api/auth/me", headers=auth_header(token))
    assert me.status_code == 200 and me.get_json()["user"]["username"] == "faby"
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers=auth_header("fake.token.here")).status_code == 401


def test_token_signed_with_another_key_is_rejected(client, app):
    token = signup(client).get_json()["token"]
    app.config["SECRET_KEY"] = "a-different-key-that-is-also-32-bytes-long"
    assert client.get("/api/auth/me", headers=auth_header(token)).status_code == 401


def test_expired_token_is_rejected(client, app):
    app.config["TOKEN_DAYS"] = -1  # tokens made now are already expired
    token = signup(client).get_json()["token"]
    assert client.get("/api/auth/me", headers=auth_header(token)).status_code == 401


def test_premium_required(app):
    from backend.auth import premium_required

    @app.get("/test-premium")
    @premium_required
    def premium_only():
        return {"secret": "voice settings"}

    client = app.test_client()
    token = signup(client).get_json()["token"]
    assert client.get("/test-premium").status_code == 401                         # not logged in
    assert client.get("/test-premium", headers=auth_header(token)).status_code == 403  # free
    db.session.scalar(db.select(User)).subscription_tier = "premium"
    db.session.commit()
    assert client.get("/test-premium", headers=auth_header(token)).status_code == 200

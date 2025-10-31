import json


def test_signup_success(client):
    payload = {"username": "alice", "email": "alice@example.com", "password": "secret"}
    r = client.post("/auth/signup", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data


def test_signup_duplicate(client):
    payload = {"username": "bob", "email": "bob@example.com", "password": "secret"}
    r1 = client.post("/auth/signup", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/auth/signup", json=payload)
    assert r2.status_code == 400
    assert "already exists" in r2.json().get("detail", "").lower()


def test_token_and_me_flow(client):
    # signup
    client.post("/auth/signup", json={"username": "carl", "email": "carl@example.com", "password": "secret"})

    # token
    r = client.post(
        "/auth/token",
        data={"username": "carl", "password": "secret"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    # me
    r2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    me = r2.json()
    assert me["username"] == "carl"



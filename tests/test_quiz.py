def auth_token(client, username="user1", email="user1@example.com", password="secret"):
    client.post("/auth/signup", json={"username": username, "email": email, "password": password})
    r = client.post(
        "/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return r.json()["access_token"]


def test_create_question_requires_auth(client):
    r = client.post("/quiz/questions/", json={"text": "Q1", "category": "gen", "difficulty": "easy"})
    assert r.status_code in (401, 403)


def test_create_and_list_questions(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # create a few
    for i in range(3):
        r = client.post(
            "/quiz/questions/",
            json={"text": f"Question {i}", "category": "cat", "difficulty": "easy"},
            headers=headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["id"] > 0
        assert body["text"].startswith("Question")

    # list
    r = client.get("/quiz/questions/?skip=0&limit=10", headers=headers)
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert len(items) >= 3



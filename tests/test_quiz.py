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


def test_create_and_manage_categories(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create category
    r = client.post(
        "/quiz/categories/",
        json={"name": "Science", "description": "Science related questions"},
        headers=headers
    )
    assert r.status_code == 200
    category = r.json()
    assert category["id"] > 0
    assert category["name"] == "Science"

    # Get categories
    r = client.get("/quiz/categories/", headers=headers)
    assert r.status_code == 200
    categories = r.json()
    assert len(categories) > 0

    # Update category
    r = client.put(
        f"/quiz/categories/{category['id']}",
        json={"name": "Science Updated", "description": "Updated description"},
        headers=headers
    )
    assert r.status_code == 200
    updated_category = r.json()
    assert updated_category["name"] == "Science Updated"

    # Delete category
    r = client.delete(f"/quiz/categories/{category['id']}", headers=headers)
    assert r.status_code == 200

def test_create_and_list_questions(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create category first
    r = client.post(
        "/quiz/categories/",
        json={"name": "Math", "description": "Math questions"},
        headers=headers
    )
    category = r.json()

    # Create questions with category
    for i in range(3):
        r = client.post(
            "/quiz/questions/",
            json={
                "text": f"Question {i}",
                "category_id": category["id"],
                "difficulty": "easy"
            },
            headers=headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["id"] > 0
        assert body["text"].startswith("Question")

    # List all questions
    r = client.get("/quiz/questions/?skip=0&limit=10", headers=headers)
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert len(items) >= 3

    # List questions by category
    r = client.get(f"/quiz/questions/?category_id={category['id']}", headers=headers)
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert len(items) == 3  # Should only return questions from this category



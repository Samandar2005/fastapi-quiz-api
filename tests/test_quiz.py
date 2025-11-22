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


def test_update_question(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create category
    r = client.post(
        "/quiz/categories/",
        json={"name": "History", "description": "History questions"},
        headers=headers
    )
    category = r.json()

    # Create question
    r = client.post(
        "/quiz/questions/",
        json={
            "text": "Original question",
            "category_id": category["id"],
            "difficulty": "easy"
        },
        headers=headers,
    )
    assert r.status_code == 200
    question = r.json()
    question_id = question["id"]

    # Update question
    r = client.put(
        f"/quiz/questions/{question_id}",
        json={
            "text": "Updated question text",
            "difficulty": "hard"
        },
        headers=headers
    )
    assert r.status_code == 200
    updated_question = r.json()
    assert updated_question["text"] == "Updated question text"
    assert updated_question["difficulty"] == "hard"
    assert updated_question["id"] == question_id


def test_delete_question(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create category
    r = client.post(
        "/quiz/categories/",
        json={"name": "Geography", "description": "Geography questions"},
        headers=headers
    )
    category = r.json()

    # Create question
    r = client.post(
        "/quiz/questions/",
        json={
            "text": "Question to delete",
            "category_id": category["id"],
            "difficulty": "medium"
        },
        headers=headers,
    )
    assert r.status_code == 200
    question = r.json()
    question_id = question["id"]

    # Delete question
    r = client.delete(f"/quiz/questions/{question_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["message"] == "Question deleted successfully"

    # Verify question is deleted
    r = client.get(f"/quiz/questions/{question_id}", headers=headers)
    assert r.status_code == 404


def test_get_single_question(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create category
    r = client.post(
        "/quiz/categories/",
        json={"name": "Literature", "description": "Literature questions"},
        headers=headers
    )
    category = r.json()

    # Create question
    r = client.post(
        "/quiz/questions/",
        json={
            "text": "What is the capital of France?",
            "category_id": category["id"],
            "difficulty": "easy",
            "time_limit_seconds": 30
        },
        headers=headers,
    )
    assert r.status_code == 200
    question = r.json()
    question_id = question["id"]

    # Get single question
    r = client.get(f"/quiz/questions/{question_id}", headers=headers)
    assert r.status_code == 200
    retrieved_question = r.json()
    assert retrieved_question["id"] == question_id
    assert retrieved_question["text"] == "What is the capital of France?"
    assert retrieved_question["time_limit_seconds"] == 30


def test_create_question_with_answers(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create category
    r = client.post(
        "/quiz/categories/",
        json={"name": "Science", "description": "Science questions"},
        headers=headers
    )
    category = r.json()

    # Create question with multiple answers (including multiple correct answers)
    r = client.post(
        "/quiz/questions/",
        json={
            "text": "Which numbers are even?",
            "category_id": category["id"],
            "difficulty": "easy",
            "answers": [
                {"text": "2", "is_correct": True},
                {"text": "3", "is_correct": False},
                {"text": "4", "is_correct": True},
                {"text": "5", "is_correct": False}
            ]
        },
        headers=headers,
    )
    assert r.status_code == 200
    question = r.json()
    assert question["id"] > 0
    assert len(question["answers"]) == 4
    
    # Check that multiple correct answers are supported
    correct_answers = [a for a in question["answers"] if a["is_correct"]]
    assert len(correct_answers) == 2
    assert any(a["text"] == "2" for a in correct_answers)
    assert any(a["text"] == "4" for a in correct_answers)


def test_create_and_manage_answers(client):
    import time
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create category with unique name
    unique_name = f"Math_{int(time.time() * 1000)}"
    r = client.post(
        "/quiz/categories/",
        json={"name": unique_name, "description": "Math questions"},
        headers=headers
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    category = r.json()
    assert "id" in category, f"Category response missing 'id': {category}"

    # Create question without answers
    r = client.post(
        "/quiz/questions/",
        json={
            "text": "What is 2 + 2?",
            "category_id": category["id"],
            "difficulty": "easy"
        },
        headers=headers,
    )
    assert r.status_code == 200
    question = r.json()
    question_id = question["id"]

    # Create first answer
    r = client.post(
        f"/quiz/questions/{question_id}/answers/",
        json={"text": "4", "is_correct": True},
        headers=headers
    )
    assert r.status_code == 200
    answer1 = r.json()
    assert answer1["text"] == "4"
    assert answer1["is_correct"] is True
    assert answer1["question_id"] == question_id

    # Create second answer
    r = client.post(
        f"/quiz/questions/{question_id}/answers/",
        json={"text": "5", "is_correct": False},
        headers=headers
    )
    assert r.status_code == 200
    answer2 = r.json()
    assert answer2["text"] == "5"
    assert answer2["is_correct"] is False

    # Get all answers for question
    r = client.get(f"/quiz/questions/{question_id}/answers/", headers=headers)
    assert r.status_code == 200
    answers = r.json()
    assert len(answers) == 2

    # Update answer
    answer_id = answer2["id"]
    r = client.put(
        f"/quiz/answers/{answer_id}",
        json={"text": "6", "is_correct": False},
        headers=headers
    )
    assert r.status_code == 200
    updated_answer = r.json()
    assert updated_answer["text"] == "6"
    assert updated_answer["is_correct"] is False

    # Get single answer
    r = client.get(f"/quiz/answers/{answer_id}", headers=headers)
    assert r.status_code == 200
    retrieved_answer = r.json()
    assert retrieved_answer["id"] == answer_id
    assert retrieved_answer["text"] == "6"

    # Delete answer
    r = client.delete(f"/quiz/answers/{answer_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["message"] == "Answer deleted successfully"

    # Verify answer is deleted
    r = client.get(f"/quiz/answers/{answer_id}", headers=headers)
    assert r.status_code == 404

    # Verify question still has one answer
    r = client.get(f"/quiz/questions/{question_id}/answers/", headers=headers)
    assert r.status_code == 200
    remaining_answers = r.json()
    assert len(remaining_answers) == 1


def test_update_answer_partial(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create category and question
    r = client.post(
        "/quiz/categories/",
        json={"name": "Test", "description": "Test questions"},
        headers=headers
    )
    category = r.json()

    r = client.post(
        "/quiz/questions/",
        json={
            "text": "Test question",
            "category_id": category["id"],
            "difficulty": "easy"
        },
        headers=headers,
    )
    question = r.json()

    # Create answer
    r = client.post(
        f"/quiz/questions/{question['id']}/answers/",
        json={"text": "Original answer", "is_correct": False},
        headers=headers
    )
    answer = r.json()
    answer_id = answer["id"]

    # Update only text
    r = client.put(
        f"/quiz/answers/{answer_id}",
        json={"text": "Updated answer"},
        headers=headers
    )
    assert r.status_code == 200
    updated = r.json()
    assert updated["text"] == "Updated answer"
    assert updated["is_correct"] is False  # Should remain unchanged

    # Update only is_correct
    r = client.put(
        f"/quiz/answers/{answer_id}",
        json={"is_correct": True},
        headers=headers
    )
    assert r.status_code == 200
    updated = r.json()
    assert updated["text"] == "Updated answer"  # Should remain unchanged
    assert updated["is_correct"] is True


def test_question_not_found_errors(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Try to get non-existent question
    r = client.get("/quiz/questions/99999", headers=headers)
    assert r.status_code == 404

    # Try to update non-existent question
    r = client.put(
        "/quiz/questions/99999",
        json={"text": "Updated"},
        headers=headers
    )
    assert r.status_code == 404

    # Try to delete non-existent question
    r = client.delete("/quiz/questions/99999", headers=headers)
    assert r.status_code == 404


def test_answer_not_found_errors(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Try to get non-existent answer
    r = client.get("/quiz/answers/99999", headers=headers)
    assert r.status_code == 404

    # Try to update non-existent answer
    r = client.put(
        "/quiz/answers/99999",
        json={"text": "Updated"},
        headers=headers
    )
    assert r.status_code == 404

    # Try to delete non-existent answer
    r = client.delete("/quiz/answers/99999", headers=headers)
    assert r.status_code == 404


def test_create_answer_for_nonexistent_question(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Try to create answer for non-existent question
    r = client.post(
        "/quiz/questions/99999/answers/",
        json={"text": "Answer", "is_correct": True},
        headers=headers
    )
    assert r.status_code == 404



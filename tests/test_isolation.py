from fastapi.testclient import TestClient
from ..src.main import app
from ..src.api.auth import get_current_user_token

client = TestClient(app)

def mock_get_current_user_token_a():
    return {"sub": "user_a", "email": "a@example.com"}

def mock_get_current_user_token_b():
    return {"sub": "user_b", "email": "b@example.com"}

def test_isolation():
    # User A creates a todo
    app.dependency_overrides[get_current_user_token] = mock_get_current_user_token_a
    response = client.post("/api/todos/", json={"title": "User A Todo", "owner_id": "user_a", "is_completed": False})
    assert response.status_code == 200
    todo_id = response.json()["id"]
    
    # User B tries to read it (should not see it in list)
    app.dependency_overrides[get_current_user_token] = mock_get_current_user_token_b
    response = client.get("/api/todos/")
    assert response.status_code == 200
    todos = response.json()
    assert not any(t["id"] == todo_id for t in todos)
    
    # User B tries to delete it
    response = client.delete(f"/api/todos/{todo_id}")
    assert response.status_code in [403, 404]

    app.dependency_overrides = {}

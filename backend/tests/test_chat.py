from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def test_chat_requires_auth(client: TestClient):
    resp = client.post("/api/v1/chat", json={"message": "hello"})
    assert resp.status_code == 401


def test_chat_empty_message(client: TestClient, user_token_headers: dict):
    resp = client.post(
        "/api/v1/chat",
        json={"message": ""},
        headers=user_token_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Message cannot be empty"


@patch("app.api.v1.endpoints.chat.run_chat")
def test_chat_success(mock_run_chat, client: TestClient, user_token_headers: dict):
    mock_run_chat.return_value = ("I can help you find products!", [], 1)

    resp = client.post(
        "/api/v1/chat",
        json={"message": "show me laptops"},
        headers=user_token_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["response"] == "I can help you find products!"
    assert data["products"] == []
    assert data["conversation_id"] == 1


@patch("app.api.v1.endpoints.chat.run_chat")
def test_chat_empty_response(mock_run_chat, client: TestClient, user_token_headers: dict):
    mock_run_chat.return_value = ("", [], 2)

    resp = client.post(
        "/api/v1/chat",
        json={"message": "hello"},
        headers=user_token_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["response"] == ""
    assert data["products"] == []
    assert data["conversation_id"] == 2


@patch("app.api.v1.endpoints.chat.run_chat")
def test_chat_with_history(mock_run_chat, client: TestClient, user_token_headers: dict):
    mock_run_chat.return_value = ("Yes, your name is Royal!", [], 3)

    resp = client.post(
        "/api/v1/chat",
        json={
            "message": "what is my name?",
            "conversation_id": 5,
        },
        headers=user_token_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["response"] == "Yes, your name is Royal!"
    assert data["products"] == []
    args = mock_run_chat.call_args[0]
    assert args[2] == 5
    assert args[3] == "what is my name?"


@patch("app.api.v1.endpoints.chat.run_chat")
def test_chat_products_in_response(mock_run_chat, client: TestClient, user_token_headers: dict):
    products = [
        {
            "id": 1,
            "title": "Laptop Pro",
            "price": 999.99,
            "thumbnail": "https://cdn.dummyjson.com/laptop/thumbnail.webp",
            "rating": 4.5,
            "discount_percentage": 10,
            "brand": "TechCo",
            "description": "A powerful laptop",
            "review_count": 42,
            "stock": 10,
        }
    ]
    mock_run_chat.return_value = ("Found 1 product(s):", products, 4)

    resp = client.post(
        "/api/v1/chat",
        json={"message": "show me laptops"},
        headers=user_token_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["response"] == "Found 1 product(s):"
    assert data["products"] == products
    assert data["conversation_id"] == 4


@patch("app.api.v1.endpoints.chat.run_chat")
def test_chat_agent_error(mock_run_chat, client: TestClient, user_token_headers: dict):
    mock_run_chat.side_effect = Exception("Ollama not running")

    resp = client.post(
        "/api/v1/chat",
        json={"message": "hello"},
        headers=user_token_headers,
    )
    assert resp.status_code == 503
    assert "AI service is temporarily unavailable" in resp.json()["detail"]

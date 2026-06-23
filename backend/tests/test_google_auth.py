from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import get_password_hash

MOCK_GOOGLE_INFO = {
    "email": "googleuser@test.com",
    "first_name": "Google",
    "last_name": "User",
    "google_id": "12345",
}


class TestGoogleAuth:
    def test_google_login_creates_new_user(self, client: TestClient, db: Session):
        with patch("app.api.v1.endpoints.auth.verify_google_token", return_value=MOCK_GOOGLE_INFO):
            resp = client.post("/api/v1/auth/google", json={"id_token": "valid_token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "googleuser@test.com"
        assert data["user"]["first_name"] == "Google"
        assert data["user"]["is_verified"] is True

        user = db.query(User).filter(User.email == "googleuser@test.com").first()
        assert user is not None
        assert user.first_name == "Google"

    def test_google_login_existing_user(self, client: TestClient, db: Session):
        existing = User(
            email="googleuser@test.com",
            hashed_password=get_password_hash("existing"),
            is_active=True,
            is_verified=True,
            role="user",
            first_name="Old",
            last_name="Name",
        )
        db.add(existing)
        db.commit()

        with patch("app.api.v1.endpoints.auth.verify_google_token", return_value=MOCK_GOOGLE_INFO):
            resp = client.post("/api/v1/auth/google", json={"id_token": "valid_token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == "googleuser@test.com"
        assert data["user"]["first_name"] == "Old"

    def test_google_login_invalid_token_returns_400(self, client: TestClient, db: Session):
        with patch("app.api.v1.endpoints.auth.verify_google_token", return_value=None):
            resp = client.post("/api/v1/auth/google", json={"id_token": "bad_token"})
        assert resp.status_code == 400
        assert "Invalid Google token" in resp.json()["detail"]

    def test_google_login_token_without_email_returns_400(self, client: TestClient, db: Session):
        with patch("app.api.v1.endpoints.auth.verify_google_token", return_value={"google_id": "no_email"}):
            resp = client.post("/api/v1/auth/google", json={"id_token": "no_email_token"})
        assert resp.status_code == 400
        assert "Invalid Google token" in resp.json()["detail"]

    def test_google_login_creates_user_with_no_name(self, client: TestClient, db: Session):
        info = {"email": "noname@test.com", "first_name": "", "last_name": "", "google_id": "67890"}
        with patch("app.api.v1.endpoints.auth.verify_google_token", return_value=info):
            resp = client.post("/api/v1/auth/google", json={"id_token": "valid_token"})
        assert resp.status_code == 200
        user = db.query(User).filter(User.email == "noname@test.com").first()
        assert user is not None
        assert user.first_name is None
        assert user.last_name is None

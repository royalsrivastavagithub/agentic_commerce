from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.user import User

def test_signup_flow(client: TestClient, db: Session):
    # 1. Signup a user
    signup_payload = {
        "email": "testuser@example.com",
        "password": "strongpassword123"
    }
    
    response = client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == signup_payload["email"]
    assert data["is_active"] is True
    assert data["is_verified"] is False
    assert "id" in data
    
    # 2. Check the user in the database
    user_db = db.query(User).filter(User.email == signup_payload["email"]).first()
    assert user_db is not None
    assert user_db.is_verified is False
    assert user_db.verification_token is not None
    
    # Keep reference to the token
    token = user_db.verification_token
    
    # 3. Try to verify the email with the generated token
    verify_response = client.get(f"/api/v1/auth/verify-email?token={token}")
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert verify_data["message"] == "Email verified successfully"
    assert verify_data["email"] == signup_payload["email"]
    assert verify_data["is_verified"] is True
    
    # 4. Check the database again to see if status updated and token cleared
    db.refresh(user_db)
    assert user_db.is_verified is True
    assert user_db.verification_token is None

def test_signup_duplicate_email(client: TestClient):
    signup_payload = {
        "email": "duplicate@example.com",
        "password": "password123"
    }
    
    # First signup
    response1 = client.post("/api/v1/auth/signup", json=signup_payload)
    assert response1.status_code == 201
    
    # Second signup with same email
    response2 = client.post("/api/v1/auth/signup", json=signup_payload)
    assert response2.status_code == 400
    assert response2.json()["detail"] == "Email already registered"

def test_signup_duplicate_email_case_insensitive(client: TestClient):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "CaseTest@Example.com", "password": "pw"}
    )
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": "casetest@example.com", "password": "pw"}
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Email already registered"

def test_verify_email_invalid_token(client: TestClient):
    # Try verifying with an invalid token
    response = client.get("/api/v1/auth/verify-email?token=non_existent_token")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired verification token"

def test_signup_invalid_email(client: TestClient):
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": "not-an-email", "password": "password123"},
    )
    assert resp.status_code == 422


def test_login_nonexistent_email(client: TestClient):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anything"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid credentials"


def test_login_access_token_wrong_password(client: TestClient, db: Session):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "formtest@example.com", "password": "correctpw"},
    )
    user = db.query(User).filter(User.email == "formtest@example.com").first()
    client.get(f"/api/v1/auth/verify-email?token={user.verification_token}")

    resp = client.post(
        "/api/v1/auth/login/access-token",
        data={"username": "formtest@example.com", "password": "wrongpw"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid credentials"


def test_login_flow(client: TestClient, db: Session):
    email = "login_test@example.com"
    password = "secretpassword"
    
    # 1. Register user
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password}
    )
    assert signup_response.status_code == 201
    
    # 2. Try to log in before verification (should fail)
    login_fail_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    assert login_fail_response.status_code == 400
    assert login_fail_response.json()["detail"] == "Invalid credentials"
    
    # 3. Verify user
    user = db.query(User).filter(User.email == email).first()
    token = user.verification_token
    verify_response = client.get(f"/api/v1/auth/verify-email?token={token}")
    assert verify_response.status_code == 200
    
    # 4. Login with JSON body (should succeed)
    login_success_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    assert login_success_response.status_code == 200
    data = login_success_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # 5. Login with OAuth2 form body (should succeed)
    form_response = client.post(
        "/api/v1/auth/login/access-token",
        data={"username": email, "password": password}
    )
    assert form_response.status_code == 200
    form_data = form_response.json()
    assert "access_token" in form_data
    assert form_data["token_type"] == "bearer"
    
    # 6. Login with incorrect password (should fail)
    bad_pw_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrongpassword"}
    )
    assert bad_pw_response.status_code == 400
    assert bad_pw_response.json()["detail"] == "Invalid credentials"

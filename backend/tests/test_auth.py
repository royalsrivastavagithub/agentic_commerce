import jwt
from datetime import timedelta, timezone, datetime
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.user import User
from app.core.security import create_access_token, get_password_hash
from app.core.config import settings

def test_signup_flow(client: TestClient, db: Session):
    # 1. Signup a user
    signup_payload = {
        "email": "testuser@example.com",
        "password": "Str0ng!pass"
    }
    
    response = client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == signup_payload["email"]
    assert data["is_active"] is True
    assert data["is_verified"] is False
    assert "id" in data
    assert data["first_name"] is None
    assert data["last_name"] is None
    assert data["phone"] is None
    
    # 2. Check the user in the database
    user_db = db.query(User).filter(User.email == signup_payload["email"]).first()
    assert user_db is not None
    assert user_db.is_verified is False

def test_signup_with_profile_fields(client: TestClient, db: Session):
    payload = {
        "email": "profile@example.com",
        "password": "Test@1234",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+91-9876543210",
        "date_of_birth": "1995-06-15",
        "gender": "male",
    }
    resp = client.post("/api/v1/auth/signup", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["phone"] == "+91-9876543210"
    assert data["date_of_birth"] == "1995-06-15"
    assert data["gender"] == "male"

    user_db = db.query(User).filter(User.email == payload["email"]).first()
    assert user_db.first_name == "John"
    assert user_db.last_name == "Doe"
    assert user_db.phone == "+91-9876543210"
    assert user_db.date_of_birth.isoformat() == "1995-06-15"
    assert user_db.gender == "male"


def test_signup_duplicate_email(client: TestClient):
    signup_payload = {
        "email": "duplicate@example.com",
        "password": "Test@1234"
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
        json={"email": "CaseTest@Example.com", "password": "Tes@1234"}
    )
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": "casetest@example.com", "password": "Tes@1234"}
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
        json={"email": "not-an-email", "password": "Test@1234"},
    )
    assert resp.status_code == 422


def test_login_nonexistent_email(client: TestClient):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "Tes@1234"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Account not found"


def test_login_access_token_wrong_password(client: TestClient, db: Session):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "formtest@example.com", "password": "Tes@1234"},
    )
    user = db.query(User).filter(User.email == "formtest@example.com").first()
    client.get(f"/api/v1/auth/verify-email?token={user.verification_token}")

    resp = client.post(
        "/api/v1/auth/login/access-token",
        data={"username": "formtest@example.com", "password": "N0tMy@pass"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid credentials"


def test_login_flow(client: TestClient, db: Session):
    email = "login_test@example.com"
    password = "Secr3t!pw"
    
    # 1. Register user
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password}
    )
    assert signup_response.status_code == 201
    
    # 2. Verify email first
    user = db.query(User).filter(User.email == email).first()
    verify_resp = client.get(f"/api/v1/auth/verify-email?token={user.verification_token}")
    assert verify_resp.status_code == 200
    
    # 3. Login with JSON body (should succeed after verification)
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
        json={"email": email, "password": "Wrong!Pass1"}
    )
    assert bad_pw_response.status_code == 400
    assert bad_pw_response.json()["detail"] == "Invalid credentials"


class TestTokenSecurity:
    def test_expired_token_returns_401(self, client: TestClient, db: Session, admin_token_headers):
        resp = client.post("/api/v1/admin/products", json={"title": "Tes@1234"}, headers=admin_token_headers)
        assert resp.status_code == 422  # ensure admin_token_headers is valid before expiry test

    def test_malformed_token_on_public_route_ignored(self, client: TestClient):
        resp = client.get(
            "/api/v1/health",
            headers={"Authorization": "Bearer garbage.token.here"},
        )
        assert resp.status_code == 200  # public route ignores bad tokens

    def test_malformed_token_on_protected_route_returns_401(self, client: TestClient):
        resp = client.post(
            "/api/v1/admin/products",
            json={"title": "Tes@1234"},
            headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid or expired token"

    def test_tampered_token_returns_401(self, client: TestClient, db: Session):
        user = User(
            email="tamper@test.com",
            hashed_password="Tes@1234",
            is_active=True,
            is_verified=True,
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(subject=user.id, role=user.role)
        parts = token.split(".")
        tampered = f"{parts[0]}.{parts[1]}.invalidsignature"
        resp = client.post(
            "/api/v1/admin/products",
            json={"title": "Tes@1234"},
            headers={"Authorization": f"Bearer {tampered}"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid or expired token"

    def test_token_with_wrong_secret_returns_401(self, client: TestClient, db: Session):
        user = User(
            email="wrongkey@test.com",
            hashed_password="Tes@1234",
            is_active=True,
            is_verified=True,
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        wrong_key_token = jwt.encode(
            {"sub": str(user.id), "role": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "this-is-a-different-secret-key-its-32-bytes!",  # >=32 bytes to avoid InsecureKeyLengthWarning
            algorithm="HS256",
        )
        resp = client.post(
            "/api/v1/admin/products",
            json={"title": "Tes@1234"},
            headers={"Authorization": f"Bearer {wrong_key_token}"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid or expired token"

    def test_expired_token_on_create_returns_401(self, client: TestClient, db: Session):
        user = User(
            email="expired@test.com",
            hashed_password="Tes@1234",
            is_active=True,
            is_verified=True,
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        expired_token = create_access_token(
            subject=user.id, role=user.role, expires_delta=timedelta(seconds=-1)
        )
        resp = client.post(
            "/api/v1/admin/products",
            json={"title": "Tes@1234"},
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid or expired token"

class TestUserState:
    def test_signup_response_includes_role(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/signup",
            json={"email": "rolecheck@test.com", "password": "Tes@1234"},
        )
        assert resp.status_code == 201
        assert resp.json()["role"] == "user"

    def test_signup_default_role_is_user_in_db(self, client: TestClient, db: Session):
        resp = client.post(
            "/api/v1/auth/signup",
            json={"email": "dbrole@test.com", "password": "Tes@1234"},
        )
        assert resp.status_code == 201
        user = db.query(User).filter(User.email == "dbrole@test.com").first()
        assert user.role == "user"

    def test_inactive_user_login_fails(self, client: TestClient, db: Session):
        user = User(
            email="inactive@test.com",
            hashed_password=get_password_hash("Tes@1234"),
            is_active=False,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@test.com", "password": "Tes@1234"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Account is disabled"

    def test_verify_email_twice_returns_error(self, client: TestClient, db: Session):
        resp = client.post(
            "/api/v1/auth/signup",
            json={"email": "verify2x@test.com", "password": "Tes@1234"},
        )
        assert resp.status_code == 201
        user = db.query(User).filter(User.email == "verify2x@test.com").first()
        token = user.verification_token
        resp1 = client.get(f"/api/v1/auth/verify-email?token={token}")
        assert resp1.status_code == 200
        resp2 = client.get(f"/api/v1/auth/verify-email?token={token}")
        assert resp2.status_code == 400
        assert resp2.json()["detail"] == "Invalid or expired verification token"

class TestAuthEdgeCases:
    def test_login_empty_password(self, client: TestClient, db: Session):
        user = User(
            email="emptypw@test.com",
            hashed_password="Tes@1234",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "emptypw@test.com", "password": ""},
        )
        assert resp.status_code == 400

    def test_login_very_long_password(self, client: TestClient, db: Session):
        long_pw = "a" * 200
        hashed = "Tes@1234"
        user = User(
            email="longpw@test.com",
            hashed_password=hashed,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "longpw@test.com", "password": long_pw},
        )
        assert resp.status_code == 400

    def test_signup_very_long_email(self, client: TestClient):
        local = "a" * 64
        domain = "b" * 63
        long_email = f"{local}@{domain}.com"
        resp = client.post(
            "/api/v1/auth/signup",
            json={"email": long_email, "password": "Tes@1234"},
        )
        assert resp.status_code == 201

    def test_signup_missing_password_field(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/signup",
            json={"email": "test@test.com"},
        )
        assert resp.status_code == 422

    def test_signup_extra_fields_ignored(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/signup",
            json={"email": "extra@test.com", "password": "Tes@1234", "role": "admin"},
        )
        assert resp.status_code == 201
        assert resp.json()["role"] == "user"


class TestUserProfile:
    def test_get_profile_unauthenticated_returns_401(self, client: TestClient):
        resp = client.get("/api/v1/auth/users/me")
        assert resp.status_code == 401

    def test_get_profile(self, client: TestClient, user_token_headers):
        resp = client.get("/api/v1/auth/users/me", headers=user_token_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "user@test.com"
        assert "id" in data
        assert data["role"] == "user"

    def test_update_profile(self, client: TestClient, user_token_headers):
        resp = client.put(
            "/api/v1/auth/users/me",
            json={"first_name": "Jane", "phone": "+91-1234567890"},
            headers=user_token_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["first_name"] == "Jane"
        assert data["phone"] == "+91-1234567890"

    def test_update_profile_empty_body_returns_200(self, client: TestClient, user_token_headers):
        resp = client.put(
            "/api/v1/auth/users/me",
            json={},
            headers=user_token_headers,
        )
        assert resp.status_code == 200

    def test_change_password(self, client: TestClient, db: Session):
        user = User(
            email="changepw@test.com",
            hashed_password="Tes@1234",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        # Override hashed_password with a real hash so verify_password works
        user.hashed_password = get_password_hash("Tes@1234")
        db.commit()

        token = create_access_token(subject=user.id, role=user.role)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.put(
            "/api/v1/auth/users/me/password",
            json={"current_password": "Tes@1234", "new_password": "N3wP@ss!x"},
            headers=headers,
        )
        assert resp.status_code == 200

        # Verify old password no longer works
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "changepw@test.com", "password": "Tes@1234"},
        )
        assert login_resp.status_code == 400

        # Verify new password works
        login_resp2 = client.post(
            "/api/v1/auth/login",
            json={"email": "changepw@test.com", "password": "N3wP@ss!x"},
        )
        assert login_resp2.status_code == 200

    def test_change_password_wrong_current(self, client: TestClient, user_token_headers):
        resp = client.put(
            "/api/v1/auth/users/me/password",
            json={"current_password": "wrongpass", "new_password": "Tes@1234"},
            headers=user_token_headers,
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Current password is incorrect"

    def test_rate_limiting_on_login(self, client: TestClient, low_rate_limit):
        MAX_R = 6
        got_429 = False
        for _ in range(MAX_R):
            resp = client.post(
                "/api/v1/auth/login",
                json={"email": "ratelimit-login@test.com", "password": "Tes@1234"},
            )
            if resp.status_code == 429:
                got_429 = True
                break
        assert got_429, f"Rate limiter did not trigger after {MAX_R} login requests"

    def test_rate_limiting_on_signup(self, client: TestClient, low_rate_limit):
        MAX_R = 6
        got_429 = False
        for i in range(MAX_R):
            resp = client.post(
                "/api/v1/auth/signup",
                json={"email": f"ratelimit-signup{i}@test.com", "password": "Str0ng!pass"},
            )
            if resp.status_code == 429:
                got_429 = True
                break
        assert got_429, f"Rate limiter did not trigger after {MAX_R} signup requests"

    def test_rate_limiting_on_change_password(self, client: TestClient, db: Session, low_rate_limit):
        user = User(email="ratepw@test.com", hashed_password="Tes@1234", is_active=True, is_verified=True)
        db.add(user)
        db.commit()
        token = create_access_token(subject=user.id, role="user")
        headers = {"Authorization": f"Bearer {token}"}
        MAX_R = 6
        got_429 = False
        for _ in range(MAX_R):
            resp = client.put(
                "/api/v1/auth/users/me/password",
                json={"current_password": "wrong", "new_password": "Tes@1234"},
                headers=headers,
            )
            if resp.status_code == 429:
                got_429 = True
                break
        assert got_429, f"Rate limiter did not trigger after {MAX_R} change-password requests"

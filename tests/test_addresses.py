from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.address import Address
from app.models.user import User
from app.core.security import create_access_token


SAMPLE_ADDRESS = {
    "label": "Home",
    "street": "123 Main St",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "country": "India",
    "is_default": False,
    "address_type": "both",
}


def _create_user_and_get_token(db: Session, email: str, role: str = "user") -> str:
    user = User(
        email=email,
        hashed_password="x",
        is_active=True,
        is_verified=True,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_access_token(subject=user.id, role=user.role)


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestAuthz:
    def test_unauthenticated_list_returns_401(self, client: TestClient):
        resp = client.get("/api/v1/users/me/addresses")
        assert resp.status_code == 401

    def test_unauthenticated_create_returns_401(self, client: TestClient):
        resp = client.post("/api/v1/users/me/addresses", json=SAMPLE_ADDRESS)
        assert resp.status_code == 401

    def test_unauthenticated_update_returns_401(self, client: TestClient):
        resp = client.put("/api/v1/users/me/addresses/1", json={"label": "Work"})
        assert resp.status_code == 401

    def test_unauthenticated_delete_returns_401(self, client: TestClient):
        resp = client.delete("/api/v1/users/me/addresses/1")
        assert resp.status_code == 401

    def test_unauthenticated_set_default_returns_401(self, client: TestClient):
        resp = client.put("/api/v1/users/me/addresses/1/default")
        assert resp.status_code == 401


class TestListAddresses:
    def test_empty_list(self, client: TestClient, db: Session):
        token = _create_user_and_get_token(db, "list_empty@test.com")
        resp = client.get("/api/v1/users/me/addresses", headers=_auth_headers(token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_only_own_addresses(self, client: TestClient, db: Session):
        token1 = _create_user_and_get_token(db, "user1@test.com")
        token2 = _create_user_and_get_token(db, "user2@test.com")

        # user1 creates an address
        resp = client.post(
            "/api/v1/users/me/addresses",
            json=SAMPLE_ADDRESS,
            headers=_auth_headers(token1),
        )
        assert resp.status_code == 201

        # user2 should see empty list
        resp2 = client.get("/api/v1/users/me/addresses", headers=_auth_headers(token2))
        assert resp2.status_code == 200
        assert resp2.json() == []


class TestCreateAddress:
    def test_create_minimal(self, client: TestClient, db: Session):
        token = _create_user_and_get_token(db, "create_min@test.com")
        payload = {
            "street": "456 Oak Ave",
            "city": "Delhi",
            "state": "Delhi",
            "pincode": "110001",
        }
        resp = client.post(
            "/api/v1/users/me/addresses",
            json=payload,
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["street"] == "456 Oak Ave"
        assert data["city"] == "Delhi"
        assert data["label"] == "Home"  # default
        assert data["country"] == "India"  # default
        assert data["address_type"] == "both"  # default
        assert data["is_default"] is False
        assert "id" in data
        assert "user_id" in data

    def test_create_full(self, client: TestClient, db: Session):
        token = _create_user_and_get_token(db, "create_full@test.com")
        payload = {
            "label": "Office",
            "street": "789 Business Park",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": "560001",
            "country": "India",
            "is_default": True,
            "address_type": "shipping",
        }
        resp = client.post(
            "/api/v1/users/me/addresses",
            json=payload,
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["label"] == "Office"
        assert data["is_default"] is True
        assert data["address_type"] == "shipping"

    def test_create_default_unsets_previous_default(self, client: TestClient, db: Session):
        token = _create_user_and_get_token(db, "default_unset@test.com")

        # Create first address (default)
        addr1 = client.post(
            "/api/v1/users/me/addresses",
            json={**SAMPLE_ADDRESS, "is_default": True},
            headers=_auth_headers(token),
        ).json()
        assert addr1["is_default"] is True

        # Create second address (default)
        addr2 = client.post(
            "/api/v1/users/me/addresses",
            json={**SAMPLE_ADDRESS, "street": "Other St", "is_default": True},
            headers=_auth_headers(token),
        ).json()
        assert addr2["is_default"] is True

        # First address should no longer be default
        resp = client.get("/api/v1/users/me/addresses", headers=_auth_headers(token))
        addrs = {a["id"]: a for a in resp.json()}
        assert addrs[addr1["id"]]["is_default"] is False
        assert addrs[addr2["id"]]["is_default"] is True

    def test_create_missing_required_field_returns_422(self, client: TestClient, db: Session):
        token = _create_user_and_get_token(db, "missing@test.com")
        resp = client.post(
            "/api/v1/users/me/addresses",
            json={"city": "Mumbai"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 422


class TestUpdateAddress:
    def test_partial_update(self, client: TestClient, db: Session):
        token = _create_user_and_get_token(db, "update_partial@test.com")
        created = client.post(
            "/api/v1/users/me/addresses",
            json=SAMPLE_ADDRESS,
            headers=_auth_headers(token),
        ).json()

        resp = client.put(
            f"/api/v1/users/me/addresses/{created['id']}",
            json={"label": "Work"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["label"] == "Work"
        assert resp.json()["street"] == SAMPLE_ADDRESS["street"]  # unchanged

    def test_full_update(self, client: TestClient, db: Session):
        token = _create_user_and_get_token(db, "update_full@test.com")
        created = client.post(
            "/api/v1/users/me/addresses",
            json=SAMPLE_ADDRESS,
            headers=_auth_headers(token),
        ).json()

        new_data = {
            "label": "Vacation Home",
            "street": "999 Beach Road",
            "city": "Goa",
            "state": "Goa",
            "pincode": "403001",
            "country": "India",
            "is_default": True,
            "address_type": "billing",
        }
        resp = client.put(
            f"/api/v1/users/me/addresses/{created['id']}",
            json=new_data,
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        for k, v in new_data.items():
            assert resp.json()[k] == v

    def test_update_other_users_address_returns_404(self, client: TestClient, db: Session):
        token1 = _create_user_and_get_token(db, "other1@test.com")
        token2 = _create_user_and_get_token(db, "other2@test.com")

        created = client.post(
            "/api/v1/users/me/addresses",
            json=SAMPLE_ADDRESS,
            headers=_auth_headers(token1),
        ).json()

        resp = client.put(
            f"/api/v1/users/me/addresses/{created['id']}",
            json={"label": "Hacked"},
            headers=_auth_headers(token2),
        )
        assert resp.status_code == 404

    def test_update_nonexistent_returns_404(self, client: TestClient, db: Session):
        token = _create_user_and_get_token(db, "nonexistent_update@test.com")
        resp = client.put(
            "/api/v1/users/me/addresses/99999",
            json={"label": "Nowhere"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 404

    def test_update_empty_city_returns_200(self, client: TestClient, db: Session):
        token = _create_user_and_get_token(db, "update_empty_city@test.com")
        created = client.post(
            "/api/v1/users/me/addresses",
            json=SAMPLE_ADDRESS,
            headers=_auth_headers(token),
        ).json()

        resp = client.put(
            f"/api/v1/users/me/addresses/{created['id']}",
            json={"city": ""},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["city"] == ""


class TestDeleteAddress:
    def test_delete_own_address(self, client: TestClient, db: Session):
        token = _create_user_and_get_token(db, "delete_own@test.com")
        created = client.post(
            "/api/v1/users/me/addresses",
            json=SAMPLE_ADDRESS,
            headers=_auth_headers(token),
        ).json()

        resp = client.delete(
            f"/api/v1/users/me/addresses/{created['id']}",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 204

        # Verify it's gone
        get_resp = client.get("/api/v1/users/me/addresses", headers=_auth_headers(token))
        assert get_resp.json() == []

    def test_delete_other_users_address_returns_404(self, client: TestClient, db: Session):
        token1 = _create_user_and_get_token(db, "del_other1@test.com")
        token2 = _create_user_and_get_token(db, "del_other2@test.com")

        created = client.post(
            "/api/v1/users/me/addresses",
            json=SAMPLE_ADDRESS,
            headers=_auth_headers(token1),
        ).json()

        resp = client.delete(
            f"/api/v1/users/me/addresses/{created['id']}",
            headers=_auth_headers(token2),
        )
        assert resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, client: TestClient, db: Session):
        token = _create_user_and_get_token(db, "del_nonexist@test.com")
        resp = client.delete(
            "/api/v1/users/me/addresses/99999",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 404


class TestSetDefault:
    def test_set_default_unsets_previous_default(self, client: TestClient, db: Session):
        token = _create_user_and_get_token(db, "set_default@test.com")

        addr1 = client.post(
            "/api/v1/users/me/addresses",
            json={**SAMPLE_ADDRESS, "is_default": True},
            headers=_auth_headers(token),
        ).json()

        addr2 = client.post(
            "/api/v1/users/me/addresses",
            json={**SAMPLE_ADDRESS, "street": "Second St"},
            headers=_auth_headers(token),
        ).json()

        # Set addr2 as default
        resp = client.put(
            f"/api/v1/users/me/addresses/{addr2['id']}/default",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["is_default"] is True

        # addr1 should no longer be default
        addrs = client.get("/api/v1/users/me/addresses", headers=_auth_headers(token)).json()
        addr_map = {a["id"]: a for a in addrs}
        assert addr_map[addr1["id"]]["is_default"] is False
        assert addr_map[addr2["id"]]["is_default"] is True

    def test_set_other_users_address_default_returns_404(self, client: TestClient, db: Session):
        token1 = _create_user_and_get_token(db, "def_other1@test.com")
        token2 = _create_user_and_get_token(db, "def_other2@test.com")

        created = client.post(
            "/api/v1/users/me/addresses",
            json=SAMPLE_ADDRESS,
            headers=_auth_headers(token1),
        ).json()

        resp = client.put(
            f"/api/v1/users/me/addresses/{created['id']}/default",
            headers=_auth_headers(token2),
        )
        assert resp.status_code == 404

    def test_set_nonexistent_default_returns_404(self, client: TestClient, db: Session):
        token = _create_user_and_get_token(db, "def_nonexist@test.com")
        resp = client.put(
            "/api/v1/users/me/addresses/99999/default",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 404

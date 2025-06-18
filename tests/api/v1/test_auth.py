import pytest
from fastapi.testclient import TestClient
from main import app

pytestmark = pytest.mark.auth

@pytest.fixture
def user_data():
    return {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }

@pytest.fixture
def register_user(client, user_data):
    response = client.post("/api/v1/auth/register", json=user_data)
    return response

@pytest.fixture
def client():
    from main import app
    return TestClient(app)

def test_login_invalid(client):
    response = client.post("/api/v1/auth/login", data={"username": "fake", "password": "fake"})
    assert response.status_code in (400, 401)

def test_register_missing_fields(client):
    response = client.post("/api/v1/auth/register", json={})
    assert response.status_code == 422

def test_confirm_email_no_token(client):
    response = client.get("/api/v1/auth/confirm-email")
    assert response.status_code == 422

def test_resend_confirmation_missing_fields(client):
    response = client.post("/api/v1/auth/resend-confirmation", json={})
    assert response.status_code == 422

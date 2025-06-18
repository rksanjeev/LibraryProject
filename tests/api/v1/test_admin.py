import pytest
from fastapi.testclient import TestClient
from main import app

pytestmark = pytest.mark.rental

client = TestClient(app)

@pytest.fixture
def staff_user_data():
    return {
        "email": "staff@example.com",
        "username": "staffuser",
        "password": "staffpassword123"
    }

@pytest.fixture
def user_data():
    return {
        "email": "user@example.com",
        "username": "user1",
        "password": "userpassword123"
    }

@pytest.fixture
def register_staff_user(client, staff_user_data):
    response = client.post("/api/v1/auth/register", json=staff_user_data)
    # Here you would promote the user to staff in the DB directly or via an endpoint
    return response

@pytest.fixture
def register_user(client, user_data):
    response = client.post("/api/v1/auth/register", json=user_data)
    return response

@pytest.fixture
def auth_headers(client, user_data, register_user):
    login = client.post("/api/v1/auth/login", data={"username": user_data["username"], "password": user_data["password"]})
    token = login.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def staff_auth_headers(client, staff_user_data, register_staff_user):
    login = client.post("/api/v1/auth/login", data={"username": staff_user_data["username"], "password": staff_user_data["password"]})
    token = login.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

def create_book(client, staff_auth_headers):
    # Simulate bulk upload with a single book row
    csv_content = "ISBN,Authors,Publication Year,Title,Language\n1234567890,Author Name,2020,Test Book,EN"
    response = client.post(
        "/api/v1/admin/books/bulk-create",
        headers=staff_auth_headers,
        files={"file": ("books.csv", csv_content.encode(), "text/csv")}
    )
    assert response.status_code == 200
    return 1  # Assuming first book gets ID 1

def test_rent_book_success(client, staff_auth_headers, auth_headers, register_user, register_staff_user):
    book_id = create_book(client, staff_auth_headers)
    # Rent the book to the user (user_id=2, book_id=1)
    response = client.post(
        "/api/v1/admin/rental",
        headers=staff_auth_headers,
        json={"user": 2, "books": book_id}
    )
    assert response.status_code == 200
    assert "Book rented successfully" in response.text

def test_return_rental_success(client, staff_auth_headers, register_user, register_staff_user):
    book_id = create_book(client, staff_auth_headers)
    # Rent the book first
    client.post(
        "/api/v1/admin/rental",
        headers=staff_auth_headers,
        json={"user": 2, "books": book_id}
    )
    # Return the book
    response = client.post(
        "/api/v1/admin/rental/return",
        headers=staff_auth_headers,
        json={"user": 2, "books": book_id}
    )
    assert response.status_code == 200
    assert "Rental returned" in response.text

def test_extend_rental_success(client, staff_auth_headers, register_user, register_staff_user):
    book_id = create_book(client, staff_auth_headers)
    # Rent the book first
    client.post(
        "/api/v1/admin/rental",
        headers=staff_auth_headers,
        json={"user": 2, "books": book_id}
    )
    # Extend the rental
    response = client.post(
        "/api/v1/admin/rental/extend",
        headers=staff_auth_headers,
        json={"user": 2, "books": book_id}
    )
    assert response.status_code == 200
    assert "Rental due date extension notification sent" in response.text

def test_rental_report_success(client, staff_auth_headers, register_user, register_staff_user):
    response = client.get("/api/v1/admin/rental/report", headers=staff_auth_headers)
    assert response.status_code == 200
    assert "report" in response.json()

def test_rent_book_unauthorized(client):
    # Should fail without staff token
    response = client.post("/api/v1/admin/rental", json={"user": 1, "books": 1})
    assert response.status_code == 401 or response.status_code == 403

def test_rent_book_missing_fields(staff_auth_headers):
    response = client.post("/api/v1/admin/rental", headers=staff_auth_headers, json={})
    assert response.status_code == 422 or response.status_code == 400

def test_return_rental_unauthorized(client):
    response = client.post("/api/v1/admin/rental/return", json={"user": 1, "books": 1})
    assert response.status_code == 401 or response.status_code == 403

def test_extend_rental_unauthorized(client):
    response = client.post("/api/v1/admin/rental/extend", json={"user": 1, "books": 1})
    assert response.status_code == 401 or response.status_code == 403

def test_rental_report_unauthorized(client):
    response = client.get("/api/v1/admin/rental/report")
    assert response.status_code == 401 or response.status_code == 403

def test_bulk_upload_invalid_file(staff_auth_headers):
    response = client.post(
        "/api/v1/admin/books/bulk-create",
        headers=staff_auth_headers,
        files={"file": ("test.txt", b"not a csv", "text/plain")}
    )
    assert response.status_code == 400

def test_confirm_staff_access_invalid_token(client):
    response = client.get("/api/v1/admin/confirm-staff-access?token=invalidtoken")
    assert response.status_code in (400, 401, 422, 403)

def test_confirm_staff_access_missing_token(client):
    response = client.get("/api/v1/admin/confirm-staff-access")
    assert response.status_code == 422

def test_rental_report_with_username(client, staff_auth_headers):
    response = client.get("/api/v1/admin/rental/report?username=2", headers=staff_auth_headers)
    assert response.status_code == 200
    assert "Rental report for user" in response.text or "report" in response.json()

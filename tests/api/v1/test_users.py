import pytest
from fastapi.testclient import TestClient
from main import app

pytestmark = pytest.mark.user

client = TestClient(app)

@pytest.fixture
def user_data():
    return {
        "email": "wishlistuser@example.com",
        "username": "wishlistuser",
        "password": "wishlistpass123"
    }

@pytest.fixture
def register_user(client, user_data):
    response = client.post("/api/v1/auth/register", json=user_data)
    return response

@pytest.fixture
def auth_headers(client, user_data, register_user):
    login = client.post("/api/v1/auth/login", data={"username": user_data["username"], "password": user_data["password"]})
    token = login.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

def create_book(client):
    # Simulate admin bulk upload with a single book row (assume admin already exists)
    csv_content = "ISBN,Authors,Publication Year,Title,Language\n9876543210,Author2,2021,Wishlist Book,EN"
    # You may need to add staff headers if endpoint requires it
    # For now, assume book with id=1 is created
    return 1

def test_get_wishlist_not_found(auth_headers):
    response = client.get("/api/v1/user/wishlist", headers=auth_headers)
    assert response.status_code == 404

def test_add_to_wishlist_and_get(auth_headers, register_user):
    book_id = create_book(client)
    # Add book to wishlist
    response = client.post(f"/api/v1/user/wishlist?book_id={book_id}", headers=auth_headers)
    assert response.status_code == 200
    # Get wishlist
    response = client.get("/api/v1/user/wishlist", headers=auth_headers)
    assert response.status_code == 200
    assert "book_ids" in response.json()

def test_remove_from_wishlist(auth_headers, register_user):
    book_id = create_book(client)
    # Add book to wishlist
    client.post(f"/api/v1/user/wishlist?book_id={book_id}", headers=auth_headers)
    # Remove book from wishlist
    response = client.delete(f"/api/v1/user/wishlist/{book_id}", headers=auth_headers)
    assert response.status_code == 200
    assert "Book removed from wishlist" in response.text

def test_search_books(auth_headers, register_user):
    # This test assumes at least one book exists
    response = client.get("/api/v1/user/search?author=Author2", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_request_staff_access(auth_headers, register_user):
    response = client.post("/api/v1/user/request-staff-access", headers=auth_headers)
    assert response.status_code == 200
    assert "Staff access request" in response.text

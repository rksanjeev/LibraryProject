# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from main import app  # or from app.main import app if your app is in app/main.py

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
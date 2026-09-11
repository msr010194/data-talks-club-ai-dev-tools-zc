import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.store import store


@pytest.fixture(autouse=True)
def reset_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture
def client():
    return TestClient(app)

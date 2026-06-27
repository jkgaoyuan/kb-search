import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from app.main import app
from app.database import get_session
from app.models.user import User
from app.models.category import Category
from app.models.document import Document
from app.utils.security import get_password_hash

# Create in-memory test database
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def override_get_session():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def auth_headers():
    # Create user
    with Session(engine) as session:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass123"),
            is_active=True
        )
        session.add(user)
        session.commit()

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_category(auth_headers):
    response = client.post(
        "/api/v1/categories",
        data={"name": "技术", "sort_order": 0},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "技术"

    # Update
    cat_id = data["id"]
    response = client.put(
        f"/api/v1/categories/{cat_id}",
        data={"name": "技术栈"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "技术栈"

    # Delete
    response = client.delete(f"/api/v1/categories/{cat_id}", headers=auth_headers)
    assert response.status_code == 200

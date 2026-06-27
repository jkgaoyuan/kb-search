import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from app.main import app
from app.database import get_session
from app.models.user import User
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
def test_user():
    with Session(engine) as session:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass123"),
            is_active=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert "checks" in data


def test_register_login():
    # Register
    response = client.post(
        "/api/v1/auth/register",
        data={"username": "newuser", "password": "newpass123"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "newuser"

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "newuser", "password": "newpass123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_search_without_auth():
    response = client.get("/api/v1/search?q=Python")
    assert response.status_code == 200
    assert "results" in response.json()


def test_suggest():
    response = client.get("/api/v1/search/suggest?q=Py")
    assert response.status_code == 200
    assert "suggestions" in response.json()


def test_hot_searches():
    response = client.get("/api/v1/search/hot")
    assert response.status_code == 200
    assert "searches" in response.json()


def test_correct_query():
    response = client.get("/api/v1/search/correct?q=Pythn")
    assert response.status_code == 200
    data = response.json()
    assert "original" in data
    assert "suggestions" in data


def test_list_categories():
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    assert "items" in response.json()


def test_create_and_delete_category():
    # Create
    response = client.post(
        "/api/v1/categories",
        data={"name": "测试分类", "sort_order": 0}
    )
    assert response.status_code == 200
    cat_id = response.json()["id"]

    # Update
    response = client.put(
        f"/api/v1/categories/{cat_id}",
        data={"name": "更新后的分类"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "更新后的分类"

    # Delete
    response = client.delete(f"/api/v1/categories/{cat_id}")
    assert response.status_code == 200


def test_tags_list():
    response = client.get("/api/v1/tags")
    assert response.status_code == 200
    assert "items" in response.json()


def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text or "python_info" in response.text

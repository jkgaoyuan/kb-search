import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from app.main import app
from app.database import get_session

# Test database URL (use SQLite for quick tests, or override for PostgreSQL)
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def override_get_session():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def db_session():
    with Session(engine) as session:
        yield session


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]


def test_ready():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200


def test_register_login():
    resp = client.post("/api/v1/auth/register", data={"username": "u1", "password": "p123456"})
    assert resp.status_code == 200

    resp = client.post("/api/v1/auth/login", data={"username": "u1", "password": "p123456"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_search_no_auth():
    resp = client.get("/api/v1/search?q=hello")
    assert resp.status_code == 200
    assert resp.json()["query"] == "hello"


def test_tags_list():
    resp = client.get("/api/v1/tags")
    assert resp.status_code == 200
    assert "items" in resp.json()

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from app.main import app
from app.database import get_session
from app.config import get_settings

settings = get_settings()

# Use in-memory SQLite for tests (or override to test DB)
TEST_DATABASE_URL = "postgresql://kb:kb@localhost:5432/kb_test"

engine = create_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)


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


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert "checks" in data


def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.1.0"


def test_register_and_login():
    """测试用户注册和登录流程"""
    # Register
    response = client.post(
        "/api/v1/auth/register",
        data={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_search_without_auth():
    """测试搜索接口无需认证"""
    response = client.get("/api/v1/search?q=test")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "results" in data


def test_tags_api():
    """测试标签云接口"""
    response = client.get("/api/v1/tags")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_metrics_endpoint():
    """测试 Prometheus 指标端点"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")

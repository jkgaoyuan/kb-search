import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import TSVECTOR
from app.main import app
from app.database import get_session
from app.models.user import User
from app.models.category import Category
from app.models.document import Document
from app.utils.security import get_password_hash
from unittest.mock import MagicMock, patch


# SQLite 不支持 PostgreSQL 的 TSVECTOR 类型。
# 使用 SQLAlchemy 的 compiles 扩展，在 SQLite 方言中将 TSVECTOR 编译为 TEXT，
# 使测试环境（内存 SQLite）可以正常创建 documents 表。
# 注意：测试中的搜索路由已通过 mock_search_service 完全 mock，不依赖真实全文搜索。
@compiles(TSVECTOR, 'sqlite')
def compile_tsvector_sqlite(element, compiler, **kw):
    return "TEXT"


# In-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def override_get_session():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """每个测试函数独立创建/销毁表，避免 SQLite 内存数据库连接状态竞争"""
    with engine.begin() as conn:
        SQLModel.metadata.create_all(conn)
    yield
    with engine.begin() as conn:
        SQLModel.metadata.drop_all(conn)


@pytest.fixture(scope="session")
def client():
    """TestClient 作为 fixture，确保在 setup_db 之后使用，避免模块级别生命周期冲突"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    with Session(engine) as session:
        yield session


@pytest.fixture
def test_user(db_session):
    """Create a normal test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session):
    """Create an admin test user"""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_inactive_user(db_session):
    """Create an inactive test user"""
    user = User(
        username="inactive",
        email="inactive@example.com",
        hashed_password=get_password_hash("pass123"),
        is_active=False,
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authorization headers for normal user"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, test_admin):
    """Get authorization headers for admin user"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "adminpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_headers(client, db_session):
    """Get authorization headers for another user (for privilege testing)"""
    user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=get_password_hash("otherpass123"),
        is_active=True,
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "otheruser", "password": "otherpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_category(db_session):
    """Create a root category"""
    category = Category(name="技术", parent_id=None, path="", sort_order=0)
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def test_subcategory(db_session, test_category):
    """Create a sub-category"""
    category = Category(
        name="后端",
        parent_id=test_category.id,
        path=f"{test_category.id}",
        sort_order=1,
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def test_document(db_session, test_user, test_category):
    """Create a test document"""
    doc = Document(
        title="Python教程",
        content="Python is a great programming language.",
        content_html="<p>Python is a great programming language.</p>",
        category_id=test_category.id,
        author_id=test_user.id,
        tags=["Python", "后端"],
        status="published",
        view_count=10,
        file_type="markdown",
        file_size=1024,
        parse_status="completed",
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.fixture
def mock_search_service():
    """Mock SearchService for SQLite compatibility (no TSVECTOR support)"""
    with patch("app.routers.search.SearchService") as MockService:
        instance = MagicMock()
        instance.search.return_value = (
            [
                {
                    "id": 1,
                    "title": "Python教程",
                    "title_highlighted": "<mark>Python</mark>教程",
                    "summary": "Python is great...",
                    "content_highlighted": "<mark>Python</mark> is great...",
                    "category_id": 1,
                    "author_id": 1,
                    "tags": ["Python"],
                    "view_count": 10,
                    "relevance_score": 0.5,
                    "updated_at": "2026-06-27T00:00:00",
                }
            ],
            1,
        )
        instance.suggest.return_value = ["Python", "Pythonic"]
        instance.get_hot_searches.return_value = [
            {"query": "Python", "count": 5}
        ]
        instance.correct_query.return_value = {
            "has_correction": False,
            "corrected": None,
        }
        MockService.return_value = instance
        yield instance

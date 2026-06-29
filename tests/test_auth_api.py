"""Auth API Tests - Full Coverage

Test cases: AUTH-001 ~ AUTH-015
Coverage: register, login, refresh, delete user
Boundary: password length 6/72 bytes
Exception: duplicate user, wrong password, inactive user, invalid token
Permission: token required for refresh
"""
import pytest
from sqlmodel import select
from app.models.user import User


class TestRegister:
    """Registration Tests (AUTH-001 ~ AUTH-007)"""

    def test_register_with_email(self, client):
        """AUTH-001: 正常注册（含邮箱）"""
        response = client.post(
            "/api/v1/auth/register",
            data={
                "username": "newuser",
                "password": "testpass123",
                "email": "new@example.com",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["message"] == "注册成功"
        assert "id" in data

    def test_register_without_email(self, client):
        """AUTH-002: 正常注册（无邮箱）"""
        response = client.post(
            "/api/v1/auth/register",
            data={
                "username": "noemailuser",
                "password": "pass123",
            },
        )
        assert response.status_code == 200
        assert response.json()["username"] == "noemailuser"

    def test_register_duplicate_username(self, client):
        """AUTH-003: 用户名已存在"""
        # First register
        client.post(
            "/api/v1/auth/register",
            data={"username": "dupuser", "password": "pass123"},
        )
        # Second register with same username
        response = client.post(
            "/api/v1/auth/register",
            data={"username": "dupuser", "password": "newpass123"},
        )
        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]

    def test_register_password_too_short(self, client):
        """AUTH-004: 密码过短（5字符）"""
        response = client.post(
            "/api/v1/auth/register",
            data={"username": "shortpw", "password": "12345"},
        )
        assert response.status_code == 400
        assert "密码过短" in response.json()["detail"]

    def test_register_password_too_long_73_bytes(self, client):
        """AUTH-005: 密码过长（73字节）"""
        long_password = "a" * 73
        response = client.post(
            "/api/v1/auth/register",
            data={"username": "longpw", "password": long_password},
        )
        assert response.status_code == 400
        assert "密码过长" in response.json()["detail"]

    def test_register_password_boundary_72_bytes(self, client):
        """AUTH-006: 密码长度边界-72字节通过"""
        boundary_password = "a" * 72
        response = client.post(
            "/api/v1/auth/register",
            data={"username": "boundarypw", "password": boundary_password},
        )
        assert response.status_code == 200

    def test_register_empty_username(self, client):
        """AUTH-007: 空用户名（必填）"""
        response = client.post(
            "/api/v1/auth/register",
            data={"username": "", "password": "pass123"},
        )
        assert response.status_code == 422


class TestLogin:
    """Login Tests (AUTH-008 ~ AUTH-011, AUTH-015)"""

    @pytest.mark.order(1)
    def test_delete_default_user(self, test_user, db_session):
        """AUTH-015: 删除默认配置的用户（必须首先执行）

        删除 test_user fixture 创建的默认用户，验证后续登录测试
        仍能正常工作（test_user 为 function scope，会自动重建）。
        """
        # 记录用户 ID
        user_id = test_user.id
        username = test_user.username

        # 从数据库中删除该用户
        db_session.delete(test_user)
        db_session.commit()

        # 验证用户已删除
        result = db_session.exec(select(User).where(User.id == user_id)).first()
        assert result is None, "用户应已被删除"

        # 再次确认通过用户名查询不到
        result_by_name = db_session.exec(select(User).where(User.username == username)).first()
        assert result_by_name is None, "通过用户名查询应无结果"

    def test_login_success(self, client, test_user):
        """AUTH-008: 正常登录"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800

    def test_login_wrong_password(self, client, test_user):
        """AUTH-009: 密码错误"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "wrongpass"},
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_user_not_exist(self, client):
        """AUTH-010: 用户不存在"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "notexist", "password": "pass123"},
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_inactive_user(self, client, test_inactive_user):
        """AUTH-011: 用户被禁用"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "inactive", "password": "pass123"},
        )
        assert response.status_code == 400
        assert "用户已被禁用" in response.json()["detail"]


class TestRefreshToken:
    """Token Refresh Tests (AUTH-012 ~ AUTH-014)"""

    def test_refresh_success(self, client, auth_headers):
        """AUTH-012: 正常刷新 Token"""
        response = client.post(
            "/api/v1/auth/refresh",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_invalid_token(self, client):
        """AUTH-013: 无效 Token"""
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        assert "无效的token" in response.json()["detail"]

    def test_refresh_no_token(self, client):
        """AUTH-014: 无 Token"""
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 401

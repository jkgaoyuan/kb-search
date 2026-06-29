"""Categories API Tests - Full Coverage

Test cases: CAT-001 ~ CAT-013
Coverage: list (tree/flat), breadcrumb, create, update, delete
Exception: 404 (not found), 400 (has children/docs)
"""
import pytest
from app.models.category import Category
from app.models.document import Document
from app.utils.security import get_password_hash


class TestListCategories:
    """Category List Tests (CAT-001 ~ CAT-002)"""

    def test_list_tree_mode(self, test_category, test_subcategory, client):
        """CAT-001: 分类列表-树形模式"""
        response = client.get("/api/v1/categories?tree=true")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        for item in data["items"]:
            assert "path" in item
            assert "parent_id" in item

    def test_list_flat_mode(self, test_category, client):
        """CAT-002: 分类列表-扁平模式"""
        response = client.get("/api/v1/categories?tree=false")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestBreadcrumb:
    """Breadcrumb Tests (CAT-003 ~ CAT-004)"""

    def test_breadcrumb_normal(self, client, test_category, test_subcategory, db_session):
        """CAT-003: 正常面包屑"""
        # Create a third-level category
        cat3 = Category(name="Python", parent_id=test_subcategory.id, path=f"{test_category.id}.{test_subcategory.id}", sort_order=2)
        db_session.add(cat3)
        db_session.commit()
        db_session.refresh(cat3)

        response = client.get(f"/api/v1/categories/{cat3.id}/breadcrumb")
        assert response.status_code == 200
        data = response.json()
        assert data["category_id"] == cat3.id
        assert len(data["breadcrumbs"]) >= 1

    def test_breadcrumb_not_found(self, client):
        """CAT-004: 分类不存在"""
        response = client.get("/api/v1/categories/99999/breadcrumb")
        assert response.status_code == 404
        assert "分类不存在" in response.json()["detail"]


class TestCreateCategory:
    """Create Category Tests (CAT-005 ~ CAT-007)"""

    def test_create_root_category(self, client):
        """CAT-005: 创建根分类"""
        response = client.post(
            "/api/v1/categories",
            params={"name": "新技术", "sort_order": 0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新技术"
        assert data["path"] == ""

    def test_create_subcategory(self, test_category, client):
        """CAT-006: 创建子分类"""
        response = client.post(
            "/api/v1/categories",
            params={"name": "Python", "parent_id": test_category.id, "sort_order": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Python"
        assert data["path"] == str(test_category.id)

    def test_create_with_invalid_parent(self, client):
        """CAT-007: 父分类不存在"""
        response = client.post(
            "/api/v1/categories",
            params={"name": "test", "parent_id": 99999},
        )
        assert response.status_code == 404
        assert "父分类不存在" in response.json()["detail"]


class TestUpdateCategory:
    """Update Category Tests (CAT-008 ~ CAT-009)"""

    def test_update_normal(self, test_category, client):
        """CAT-008: 正常更新"""
        response = client.put(
            f"/api/v1/categories/{test_category.id}",
            params={"name": "更新名称", "sort_order": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新名称"

    def test_update_not_found(self, client):
        """CAT-009: 分类不存在"""
        response = client.put(
            "/api/v1/categories/99999",
            params={"name": "test"},
        )
        assert response.status_code == 404
        assert "分类不存在" in response.json()["detail"]


class TestDeleteCategory:
    """Delete Category Tests (CAT-010 ~ CAT-013)"""

    def test_delete_empty_category(self, client):
        """CAT-010: 正常删除空分类"""
        # Create an empty category
        resp = client.post(
            "/api/v1/categories",
            params={"name": "空分类", "sort_order": 0},
        )
        cat_id = resp.json()["id"]

        response = client.delete(f"/api/v1/categories/{cat_id}")
        assert response.status_code == 200
        assert "已删除" in response.json()["message"]

    def test_delete_with_children(self, test_category, test_subcategory, client):
        """CAT-011: 有子分类无法删除"""
        response = client.delete(f"/api/v1/categories/{test_category.id}")
        assert response.status_code == 400
        assert "子分类" in response.json()["detail"]

    def test_delete_with_documents(self, test_category, test_document, client):
        """CAT-012: 有关联文档无法删除"""
        response = client.delete(f"/api/v1/categories/{test_category.id}")
        assert response.status_code == 400
        assert "关联文档" in response.json()["detail"]

    def test_delete_not_found(self, client):
        """CAT-013: 分类不存在"""
        response = client.delete("/api/v1/categories/99999")
        assert response.status_code == 404
        assert "分类不存在" in response.json()["detail"]

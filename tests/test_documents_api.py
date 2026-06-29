"""Document API Tests - Full Coverage

Test cases: DOC-001 ~ DOC-029
Coverage: upload, list, detail, status, update, delete (soft delete)
Boundary: file size 20MB, page_size 100/101
Exception: 404, 400, 401, 403, 422
Permission: auth required, owner/admin only
"""
import io
import pytest


class TestUploadDocument:
    """Document Upload Tests (DOC-001 ~ DOC-008)"""

    def test_upload_markdown(self, client, auth_headers, test_category):
        """DOC-001: 正常上传 Markdown"""
        response = client.post(
            "/api/v1/documents",
            data={
                "title": "Python教程",
                "category_id": test_category.id,
                "tags": "Python,后端",
            },
            files={
                "file": ("test.md", io.BytesIO(b"# Hello World\n\nThis is markdown."), "text/markdown")
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Python教程"
        assert data["parse_status"] == "pending"
        assert "id" in data
        assert "task_id" in data

    def test_upload_html(self, client, auth_headers, test_category):
        """DOC-002: 正常上传 HTML"""
        response = client.post(
            "/api/v1/documents",
            data={
                "title": "HTML教程",
                "category_id": test_category.id,
                "tags": "前端",
            },
            files={
                "file": ("test.html", io.BytesIO(b"<html><body><h1>Test</h1></body></html>"), "text/html")
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["parse_status"] == "pending"

    def test_upload_docx(self, client, auth_headers, test_category):
        """DOC-003: 正常上传 DOCX"""
        response = client.post(
            "/api/v1/documents",
            data={
                "title": "Word文档",
                "category_id": test_category.id,
            },
            files={
                "file": ("test.docx", io.BytesIO(b"PK\x03\x04 fake docx content"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["parse_status"] == "pending"

    def test_upload_unauthorized(self, client, test_category):
        """DOC-004: 未认证上传"""
        response = client.post(
            "/api/v1/documents",
            data={
                "title": "未认证",
                "category_id": test_category.id,
            },
            files={
                "file": ("test.md", io.BytesIO(b"# Test"), "text/markdown")
            },
        )
        assert response.status_code == 401

    def test_upload_oversized_file(self, client, auth_headers, test_category):
        """DOC-005: 文件大小超过 20MB"""
        # Create a fake markdown file larger than 20MB
        big_file = io.BytesIO(b"# " + b"0" * (21 * 1024 * 1024))
        response = client.post(
            "/api/v1/documents",
            data={
                "title": "大文件",
                "category_id": test_category.id,
            },
            files={
                "file": ("big.md", big_file, "text/markdown")
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "20.0MB" in response.json()["detail"]

    def test_upload_boundary_20mb(self, client, auth_headers, test_category):
        """DOC-006: 文件大小边界-20MB 恰好通过"""
        # Create a fake markdown file exactly 20MB
        exact_20mb = io.BytesIO(b"# " + b"0" * (20 * 1024 * 1024 - 2))
        response = client.post(
            "/api/v1/documents",
            data={
                "title": "20MB边界文件",
                "category_id": test_category.id,
            },
            files={
                "file": ("exact20mb.md", exact_20mb, "text/markdown")
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["parse_status"] == "pending"
        assert "id" in data

    def test_upload_unsupported_format(self, client, auth_headers, test_category):
        """DOC-007: 不支持的文件类型"""
        response = client.post(
            "/api/v1/documents",
            data={
                "title": "不支持的格式",
                "category_id": test_category.id,
            },
            files={
                "file": ("test.txt", io.BytesIO(b"plain text"), "text/plain")
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_upload_empty_title(self, client, auth_headers, test_category):
        """DOC-008: 空标题"""
        response = client.post(
            "/api/v1/documents",
            data={
                "title": "",
                "category_id": test_category.id,
            },
            files={
                "file": ("test.md", io.BytesIO(b"# Test"), "text/markdown")
            },
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestListDocuments:
    """Document List Tests (DOC-009 ~ DOC-014)"""

    def test_list_default(self, client, test_document):
        """DOC-009: 默认分页查询"""
        response = client.get("/api/v1/documents?status=published")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_filter_by_category(self, client, test_document, test_category):
        """DOC-010: 按分类过滤"""
        response = client.get(f"/api/v1/documents?category_id={test_category.id}&status=published")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["category_id"] == test_category.id

    def test_list_filter_by_status_draft(self, client, db_session, test_user, test_category):
        """DOC-011: 按状态过滤 draft"""
        # Create a draft document directly
        from app.models.document import Document
        draft_doc = Document(
            title="草稿文档",
            content="draft content",
            content_html="<p>draft</p>",
            category_id=test_category.id,
            author_id=test_user.id,
            tags=["draft"],
            status="draft",
            view_count=0,
            file_type="markdown",
            file_size=100,
            parse_status="completed",
        )
        db_session.add(draft_doc)
        db_session.commit()

        response = client.get("/api/v1/documents?status=draft")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "draft"
        # Should not contain the published test_document
        ids = [item["id"] for item in data["items"]]
        assert draft_doc.id in ids

    def test_list_page_size_boundary_100(self, client):
        """DOC-012: 分页边界 page_size=100"""
        response = client.get("/api/v1/documents?page_size=100")
        assert response.status_code == 200
        assert len(response.json()["items"]) <= 100

    def test_list_page_size_over_boundary_101(self, client):
        """DOC-013: 分页越界 page_size=101"""
        response = client.get("/api/v1/documents?page_size=101")
        assert response.status_code == 422

    def test_list_page_zero(self, client):
        """DOC-014: 分页边界 page=0"""
        response = client.get("/api/v1/documents?page=0")
        assert response.status_code == 422


class TestDocumentDetail:
    """Document Detail Tests (DOC-015 ~ DOC-017)"""

    def test_get_document_detail(self, client, test_document):
        """DOC-015: 正常获取文档详情"""
        response = client.get(f"/api/v1/documents/{test_document.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_document.id
        assert data["title"] == test_document.title
        assert "content_html" in data

    def test_get_document_view_count_increment(self, client, test_document):
        """DOC-016: 浏览量原子递增"""
        # First request
        resp1 = client.get(f"/api/v1/documents/{test_document.id}")
        view_count_1 = resp1.json()["view_count"]

        # Second request
        resp2 = client.get(f"/api/v1/documents/{test_document.id}")
        view_count_2 = resp2.json()["view_count"]

        assert view_count_2 == view_count_1 + 1

    def test_get_document_not_found(self, client):
        """DOC-017: 文档不存在"""
        response = client.get("/api/v1/documents/99999")
        assert response.status_code == 404
        assert "文档不存在" in response.json()["detail"]


class TestDocumentStatus:
    """Document Status Tests (DOC-018 ~ DOC-019)"""

    def test_get_document_status(self, client, test_document):
        """DOC-018: 查询解析状态"""
        response = client.get(f"/api/v1/documents/{test_document.id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_document.id
        assert "parse_status" in data
        assert "content_length" in data

    def test_get_document_status_not_found(self, client):
        """DOC-019: 查询不存在文档状态"""
        response = client.get("/api/v1/documents/99999/status")
        assert response.status_code == 404


class TestUpdateDocument:
    """Document Update Tests (DOC-020 ~ DOC-024)"""

    def test_update_by_owner(self, client, auth_headers, test_document):
        """DOC-020: 正常更新（作者）"""
        response = client.put(
            f"/api/v1/documents/{test_document.id}",
            data={"title": "新标题", "tags": "新标签"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["message"] == "更新成功"

    def test_update_by_admin(self, client, admin_headers, test_document):
        """DOC-021: 正常更新（管理员）"""
        response = client.put(
            f"/api/v1/documents/{test_document.id}",
            data={"title": "管理员修改"},
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_update_unauthorized(self, client, test_document):
        """DOC-022: 未认证更新"""
        response = client.put(
            f"/api/v1/documents/{test_document.id}",
            data={"title": "未认证修改"},
        )
        assert response.status_code == 401

    def test_update_forbidden(self, client, other_user_headers, test_document):
        """DOC-023: 越权更新（非作者/非管理员）"""
        response = client.put(
            f"/api/v1/documents/{test_document.id}",
            data={"title": "越权修改"},
            headers=other_user_headers,
        )
        assert response.status_code == 403
        assert "无权修改" in response.json()["detail"]

    def test_update_not_found(self, client, auth_headers):
        """DOC-024: 更新不存在文档"""
        response = client.put(
            "/api/v1/documents/99999",
            data={"title": "test"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDeleteDocument:
    """Document Delete Tests (DOC-025 ~ DOC-029)"""

    def test_delete_by_owner(self, client, auth_headers, test_document, db_session):
        """DOC-025: 正常删除（作者软删除）"""
        response = client.delete(
            f"/api/v1/documents/{test_document.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "已归档" in response.json()["message"]

        # Verify status changed to archived
        db_session.refresh(test_document)
        assert test_document.status == "archived"

    def test_delete_by_admin(self, client, admin_headers, test_document):
        """DOC-026: 正常删除（管理员）"""
        response = client.delete(
            f"/api/v1/documents/{test_document.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_delete_unauthorized(self, client, test_document):
        """DOC-027: 未认证删除"""
        response = client.delete(f"/api/v1/documents/{test_document.id}")
        assert response.status_code == 401

    def test_delete_forbidden(self, client, other_user_headers, test_document):
        """DOC-028: 越权删除"""
        response = client.delete(
            f"/api/v1/documents/{test_document.id}",
            headers=other_user_headers,
        )
        assert response.status_code == 403
        assert "无权删除" in response.json()["detail"]

    def test_delete_not_found(self, client, auth_headers):
        """DOC-029: 删除不存在文档"""
        response = client.delete(
            "/api/v1/documents/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404

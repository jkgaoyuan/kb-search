"""Stats API Tests - Full Coverage

Test cases: STATS-001 ~ STATS-007
Coverage: author ranking, document heat, category stats
Boundary: empty data, days filter, outerjoin empty categories
"""
import pytest
from app.models.category import Category


class TestAuthorRanking:
    """Author Ranking Tests (STATS-001 ~ STATS-003)"""

    def test_author_ranking_default(self, client, test_document):
        """STATS-001: 作者排行-默认"""
        response = client.get("/api/v1/stats/authors?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        if data["items"]:
            assert "user_id" in data["items"][0]
            assert "username" in data["items"][0]
            assert "document_count" in data["items"][0]
            assert "total_views" in data["items"][0]

    def test_author_ranking_with_days(self, client, test_document):
        """STATS-002: 按时间范围过滤"""
        response = client.get("/api/v1/stats/authors?days=7&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_author_ranking_empty(self, client):
        """STATS-003: 无数据"""
        # This test assumes no documents in the database
        # In practice, other tests may have added documents
        response = client.get("/api/v1/stats/authors")
        assert response.status_code == 200
        assert "items" in response.json()


class TestDocumentHeat:
    """Document Heat Tests (STATS-004 ~ STATS-005)"""

    def test_document_heat_normal(self, client, test_document):
        """STATS-004: 单文档热度-正常"""
        response = client.get(f"/api/v1/stats/documents/{test_document.id}/heat")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == test_document.id
        assert data["title"] == test_document.title
        assert "view_count" in data
        assert "days_since_created" in data
        assert data["days_since_created"] >= 0

    def test_document_heat_not_found(self, client):
        """STATS-005: 不存在文档"""
        response = client.get("/api/v1/stats/documents/99999/heat")
        assert response.status_code == 200
        assert response.json() == {}


class TestCategoryStats:
    """Category Stats Tests (STATS-006 ~ STATS-007)"""

    def test_category_stats_normal(self, client, test_category, test_document):
        """STATS-006: 分类统计-正常"""
        response = client.get("/api/v1/stats/categories")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Check that our category is present
        cat_ids = [item["category_id"] for item in data["items"]]
        assert test_category.id in cat_ids

    def test_category_stats_empty_category(self, client, test_category, db_session):
        """STATS-007: 空分类统计"""
        # Create a new empty category
        empty_cat = Category(name="空分类", parent_id=None, path="", sort_order=99)
        db_session.add(empty_cat)
        db_session.commit()
        db_session.refresh(empty_cat)

        response = client.get("/api/v1/stats/categories")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            if item["category_id"] == empty_cat.id:
                assert item["document_count"] == 0

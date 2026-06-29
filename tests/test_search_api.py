"""Search API Tests - Full Coverage

Test cases: SEARCH-001 ~ SEARCH-015
Coverage: full-text search, suggest, hot searches, correct query
Note: SearchService uses PostgreSQL TSVECTOR which is not supported in SQLite.
We mock SearchService to enable testing in SQLite environment.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestSearch:
    """Full-text Search Tests (SEARCH-001 ~ SEARCH-008)"""

    def test_search_normal(self, client, mock_search_service):
        """SEARCH-001: 正常搜索关键词"""
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search?q=Python&sort=relevance&page=1&page_size=20")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Python"
        assert "results" in data
        assert "total" in data
        assert "correction" in data

    def test_search_empty_query(self, client, mock_search_service):
        """SEARCH-002: 空查询"""
        mock_search_service.search.return_value = ([], 0)
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search?q=")
        assert response.status_code == 200
        assert response.json()["results"] == []
        assert response.json()["total"] == 0

    def test_search_filter_by_category(self, client, mock_search_service):
        """SEARCH-003: 按分类过滤"""
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search?q=Python&category_id=1")
        assert response.status_code == 200

    def test_search_sort_by_relevance(self, client, mock_search_service):
        """SEARCH-004: 按相关度排序"""
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search?q=Python&sort=relevance")
        assert response.status_code == 200

    def test_search_sort_by_updated_at(self, client, mock_search_service):
        """SEARCH-005: 按更新时间排序"""
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search?q=Python&sort=updated_at")
        assert response.status_code == 200

    def test_search_sort_by_view_count(self, client, mock_search_service):
        """SEARCH-006: 按浏览量排序"""
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search?q=Python&sort=view_count")
        assert response.status_code == 200

    def test_search_page_size_boundary_100(self, client, mock_search_service):
        """SEARCH-007: 分页 page_size=100"""
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search?q=test&page_size=100")
        assert response.status_code == 200

    def test_search_page_size_over_boundary_101(self, client, mock_search_service):
        """SEARCH-008: 分页越界 page_size=101"""
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search?q=test&page_size=101")
        assert response.status_code == 422


class TestSearchSuggest:
    """Search Suggest Tests (SEARCH-009 ~ SEARCH-011)"""

    def test_suggest_normal(self, client, mock_search_service):
        """SEARCH-009: 正常前缀匹配"""
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search/suggest?q=Py&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Py"
        assert "suggestions" in data

    def test_suggest_short_prefix(self, client, mock_search_service):
        """SEARCH-010: 前缀过短（1字符）应返回 422"""
        mock_search_service.suggest.return_value = []
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search/suggest?q=P")
        assert response.status_code == 422

    def test_suggest_empty_query(self, client, mock_search_service):
        """SEARCH-011: 空查询"""
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search/suggest?q=")
        assert response.status_code == 422


class TestHotSearches:
    """Hot Search Tests (SEARCH-012 ~ SEARCH-013)"""

    def test_hot_searches_default(self, client, mock_search_service):
        """SEARCH-012: 默认24小时排行"""
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search/hot?limit=10&hours=24")
        assert response.status_code == 200
        data = response.json()
        assert data["period_hours"] == 24
        assert "searches" in data

    def test_hot_searches_custom_range(self, client, mock_search_service):
        """SEARCH-013: 自定义时间范围"""
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search/hot?limit=5&hours=168")
        assert response.status_code == 200
        assert len(response.json()["searches"]) <= 5


class TestSearchCorrect:
    """Search Correction Tests (SEARCH-014 ~ SEARCH-015)"""

    def test_correct_with_correction(self, client, mock_search_service):
        """SEARCH-014: 正常纠错"""
        mock_search_service.correct_query.return_value = {
            "has_correction": True,
            "corrected": "Python",
        }
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search/correct?q=Pythn")
        assert response.status_code == 200
        data = response.json()
        assert data["has_correction"] is True
        assert data["corrected"] == "Python"

    def test_correct_no_correction(self, client, mock_search_service):
        """SEARCH-015: 无需纠错"""
        mock_search_service.correct_query.return_value = {
            "has_correction": False,
            "corrected": None,
        }
        with patch("app.routers.search.SearchService", return_value=mock_search_service):
            response = client.get("/api/v1/search/correct?q=Python")
        assert response.status_code == 200
        data = response.json()
        assert data["has_correction"] is False
        assert data["corrected"] is None

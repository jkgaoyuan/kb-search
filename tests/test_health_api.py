"""Health Check API Tests - Full Coverage

Test cases: HEALTH-001 ~ HEALTH-005
Coverage: health, ready, metrics, root
"""


class TestHealth:
    """Health Check Tests"""

    def test_health_check_all_ok(self, client):
        """HEALTH-001: 健康检查-全部正常"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "degraded"]
        assert data["version"] == "0.1.0"
        assert "checks" in data

    def test_health_check_db_error(self, client):
        """HEALTH-002: 健康检查-仅 DB 异常"""
        from unittest.mock import patch
        with patch("app.routers.health.engine.connect") as mock_connect:
            mock_connect.side_effect = Exception("DB connection failed")
            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert "error" in data["checks"]["database"]

    def test_readiness_check(self, client):
        """HEALTH-003: 就绪检查"""
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["ready"] is True

    def test_metrics(self, client):
        """HEALTH-004: Prometheus 指标暴露"""
        response = client.get("/metrics")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/plain" in content_type or "application/openmetrics-text" in content_type

    def test_root(self, client):
        """HEALTH-005: 根路径信息"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "KB Search" in data["message"]
        assert data["version"] == "0.1.0"
        assert data["docs"] == "/docs"

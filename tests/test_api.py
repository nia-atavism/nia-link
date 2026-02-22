"""
Nia-Link API Endpoint Tests
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestHealthAndRoot:
    """Test system endpoints (no auth required)"""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_root_info(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Nia-Link"
        assert "version" in data

    def test_meta_origin_easter_egg(self, client):
        response = client.get("/meta-origin")
        assert response.status_code == 200
        data = response.json()
        assert "terminal" in data

    def test_stats_endpoint(self, client):
        response = client.get("/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "total_requests" in data
        assert "scrape_count" in data


class TestAuthRequired:
    """Test that protected endpoints require authentication"""

    def test_scrape_no_auth(self, client):
        response = client.post("/v1/scrape", json={"url": "https://example.com"})
        assert response.status_code == 401  # HTTPBearer returns 403 when no token

    def test_scrape_invalid_key(self, client, invalid_auth_headers):
        response = client.post(
            "/v1/scrape",
            json={"url": "https://example.com"},
            headers=invalid_auth_headers
        )
        assert response.status_code == 401

    def test_interact_no_auth(self, client):
        response = client.post("/v1/interact", json={
            "url": "https://example.com",
            "actions": [{"type": "click", "selector": "#btn"}]
        })
        assert response.status_code == 401

    def test_diff_no_auth(self, client):
        response = client.post("/v1/diff", json={"url": "https://example.com"})
        assert response.status_code == 401

    def test_queue_submit_no_auth(self, client):
        response = client.post("/v1/queue/submit", json={"url": "https://example.com"})
        assert response.status_code == 401

    def test_queue_status_no_auth(self, client):
        response = client.get("/v1/queue/some-task-id")
        assert response.status_code == 401


class TestScrapeEndpoint:
    """Test /v1/scrape with mocked scraper"""

    @patch("app.main.ScraperService")
    @patch("app.main.StatsService")
    def test_scrape_success(self, MockStats, MockScraper, client, auth_headers, mock_scraper_result):
        mock_scraper_inst = MockScraper.return_value
        mock_scraper_inst.scrape = AsyncMock(return_value=mock_scraper_result)
        mock_stats_inst = MockStats.return_value

        response = client.post(
            "/v1/scrape",
            json={"url": "https://example.com"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["content"]["title"] == "Test Page"

    @patch("app.main.ScraperService")
    @patch("app.main.StatsService")
    def test_scrape_with_options(self, MockStats, MockScraper, client, auth_headers, mock_scraper_result):
        mock_scraper_inst = MockScraper.return_value
        mock_scraper_inst.scrape = AsyncMock(return_value=mock_scraper_result)

        response = client.post(
            "/v1/scrape",
            json={
                "url": "https://example.com",
                "format": "text",
                "mode": "fast",
                "extract_actions": True
            },
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_scrape_invalid_url(self, client, auth_headers):
        response = client.post(
            "/v1/scrape",
            json={"url": "not-a-valid-url"},
            headers=auth_headers
        )
        assert response.status_code == 422  # Pydantic validation error


class TestInteractEndpoint:
    """Test /v1/interact with mocked executor"""

    @patch("app.main.StatsService")
    @patch("app.main.ExecutorService")
    def test_interact_success(self, MockExecutor, MockStats, client, auth_headers):
        mock_executor_inst = MockExecutor.return_value
        mock_executor_inst.interact = AsyncMock(return_value={
            "status": "success",
            "log": ["Synaptic-clicked #btn"],
            "screenshot": "/tmp/screenshot.png",
            "trajectory_cloud": "/tmp/trajectory.json",
            "points_captured": 25,
            "js_results": None
        })

        response = client.post(
            "/v1/interact",
            json={
                "url": "https://example.com",
                "actions": [{"type": "click", "selector": "#btn"}]
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["points_captured"] == 25

    @patch("app.main.StatsService")
    @patch("app.main.ExecutorService")
    def test_interact_error(self, MockExecutor, MockStats, client, auth_headers):
        mock_executor_inst = MockExecutor.return_value
        mock_executor_inst.interact = AsyncMock(return_value={
            "status": "error",
            "message": "Element not found",
            "log": []
        })

        response = client.post(
            "/v1/interact",
            json={
                "url": "https://example.com",
                "actions": [{"type": "click", "selector": "#nonexistent"}]
            },
            headers=auth_headers
        )
        assert response.status_code == 500


class TestQueueEndpoint:
    """Test /v1/queue/* endpoints"""

    def test_queue_status_not_found(self, client, auth_headers):
        response = client.get("/v1/queue/nonexistent-task-id", headers=auth_headers)
        assert response.status_code == 404


class TestDiffEndpoint:
    """Test /v1/diff with mocked services"""

    @patch("app.main.DiffService")
    @patch("app.main.ScraperService")
    def test_diff_first_snapshot(self, MockScraper, MockDiff, client, auth_headers, mock_scraper_result):
        mock_scraper_inst = MockScraper.return_value
        mock_scraper_inst.scrape = AsyncMock(return_value=mock_scraper_result)

        mock_diff_inst = MockDiff.return_value
        mock_diff_inst.save_snapshot = MagicMock()
        mock_diff_inst.get_diff = MagicMock(return_value={"status": "no_previous"})

        response = client.post(
            "/v1/diff",
            json={"url": "https://example.com"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "new_snapshot"

    @patch("app.main.DiffService")
    @patch("app.main.ScraperService")
    def test_diff_unchanged(self, MockScraper, MockDiff, client, auth_headers, mock_scraper_result):
        mock_scraper_inst = MockScraper.return_value
        mock_scraper_inst.scrape = AsyncMock(return_value=mock_scraper_result)

        mock_diff_inst = MockDiff.return_value
        mock_diff_inst.save_snapshot = MagicMock()
        mock_diff_inst.get_diff = MagicMock(return_value={"status": "unchanged"})

        response = client.post(
            "/v1/diff",
            json={"url": "https://example.com"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unchanged"

    @patch("app.main.DiffService")
    @patch("app.main.ScraperService")
    def test_diff_changes_detected(self, MockScraper, MockDiff, client, auth_headers, mock_scraper_result):
        mock_scraper_inst = MockScraper.return_value
        mock_scraper_inst.scrape = AsyncMock(return_value=mock_scraper_result)

        mock_diff_inst = MockDiff.return_value
        mock_diff_inst.save_snapshot = MagicMock()
        mock_diff_inst.get_diff = MagicMock(return_value={
            "status": "changed",
            "added_lines": 5,
            "removed_lines": 2,
            "diff": "+new line\n-old line",
            "summary": "5 lines added, 2 lines removed",
            "previous_timestamp": 1000000.0,
            "current_timestamp": 1000100.0
        })

        response = client.post(
            "/v1/diff",
            json={"url": "https://example.com"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "changed"
        assert data["added_lines"] == 5
        assert data["removed_lines"] == 2

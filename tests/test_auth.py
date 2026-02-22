"""
Nia-Link Authentication Tests
"""

import pytest


class TestAuthentication:
    """Test API key authentication"""

    def test_valid_api_key(self, client, auth_headers):
        """Valid key should pass auth — use scrape which requires auth"""
        from unittest.mock import patch, AsyncMock, MagicMock
        with patch("app.main.ScraperService") as MockScraper, \
             patch("app.main.StatsService"):
            mock_inst = MockScraper.return_value
            mock_inst.scrape = AsyncMock(return_value={
                "data": {"title": "T", "content": "C", "metadata": {}, "links": [], "actions": None},
                "cost": {"original_size": 100, "cleaned_size": 10, "reduction_percent": 90},
                "mode_used": "fast"
            })
            response = client.post(
                "/v1/scrape",
                json={"url": "https://example.com"},
                headers=auth_headers
            )
            assert response.status_code == 200

    def test_second_valid_key(self, client):
        """Second API key in comma-separated list should also work"""
        from unittest.mock import patch, AsyncMock
        headers = {"Authorization": "Bearer test-key-456"}
        with patch("app.main.ScraperService") as MockScraper, \
             patch("app.main.StatsService"):
            mock_inst = MockScraper.return_value
            mock_inst.scrape = AsyncMock(return_value={
                "data": {"title": "T", "content": "C", "metadata": {}, "links": [], "actions": None},
                "cost": {"original_size": 100, "cleaned_size": 10, "reduction_percent": 90},
                "mode_used": "fast"
            })
            response = client.post(
                "/v1/scrape",
                json={"url": "https://example.com"},
                headers=headers
            )
            assert response.status_code == 200

    def test_invalid_api_key_rejected(self, client, invalid_auth_headers):
        """Invalid key should be rejected with 401"""
        response = client.post(
            "/v1/scrape",
            json={"url": "https://example.com"},
            headers=invalid_auth_headers
        )
        assert response.status_code == 401

    def test_missing_auth_header_rejected(self, client):
        """Missing Authorization header should be rejected with 401"""
        response = client.post(
            "/v1/scrape",
            json={"url": "https://example.com"}
        )
        assert response.status_code == 401

    def test_malformed_auth_header(self, client):
        """Non-Bearer scheme should be rejected"""
        response = client.post(
            "/v1/scrape",
            json={"url": "https://example.com"},
            headers={"Authorization": "Basic dXNlcjpwYXNz"}
        )
        assert response.status_code in (401, 403)

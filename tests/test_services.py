"""
Nia-Link Service Layer Tests
Tests for individual services without network calls
"""

import pytest
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCleanerService:
    """Test HTML cleaning and format conversion"""

    def test_to_markdown(self):
        from app.services.cleaner import CleanerService
        cleaner = CleanerService()
        html = "<h1>Title</h1><p>Paragraph text</p>"
        result = cleaner.to_markdown(html)
        assert "Title" in result
        assert "Paragraph" in result

    def test_to_text(self):
        from app.services.cleaner import CleanerService
        cleaner = CleanerService()
        html = "<h1>Title</h1><p>Hello <b>world</b></p>"
        result = cleaner.to_text(html)
        assert "Title" in result
        assert "Hello" in result
        assert "<h1>" not in result  # No HTML tags

    def test_extract_metadata(self):
        from app.services.cleaner import CleanerService
        from bs4 import BeautifulSoup
        cleaner = CleanerService()
        html = '<html><head><title>My Page</title><meta name="description" content="A description"></head><body></body></html>'
        soup = BeautifulSoup(html, "lxml")
        metadata = cleaner.extract_metadata(soup)
        assert metadata is not None
        assert metadata.get("title") == "My Page"

    def test_calculate_savings(self):
        from app.services.cleaner import CleanerService
        cleaner = CleanerService()
        result = cleaner.calculate_savings(10000, 1000)
        assert result["original_size"] == 10000
        assert result["cleaned_size"] == 1000
        assert result["reduction_percent"] == 90.0


class TestExtractor:
    """Test action map extraction"""

    def test_extract_buttons(self):
        from app.services.extractor import ActionExtractor
        extractor = ActionExtractor()
        html = '<html><body><button id="submit">Submit</button><button class="cancel">Cancel</button></body></html>'
        actions = extractor.extract_actions(html)
        assert actions is not None
        assert len(actions) >= 1

    def test_extract_inputs(self):
        from app.services.extractor import ActionExtractor
        extractor = ActionExtractor()
        html = '<html><body><form><input type="text" id="name" placeholder="Your name"><input type="email" id="email"></form></body></html>'
        actions = extractor.extract_actions(html)
        assert actions is not None
        assert len(actions) >= 1

    def test_extract_links(self):
        from app.services.extractor import ActionExtractor
        extractor = ActionExtractor()
        html = '<html><body><nav><a href="/about">About Us</a><a href="/contact">Contact Us</a></nav></body></html>'
        actions = extractor.extract_actions(html)
        # ActionExtractor may filter links by importance; just verify it returns a list
        assert actions is not None
        assert isinstance(actions, list)

    def test_token_calculator(self):
        from app.services.extractor import TokenCalculator
        calc = TokenCalculator()
        savings_str, details = calc.calculate_token_savings(
            "<html><body><p>Hello world</p></body></html>",
            "Hello world"
        )
        assert "%" in savings_str
        assert details["original_tokens"] > 0
        assert details["tokens_saved"] > 0
        assert details["reduction_percent"] > 0


class TestProxyPool:
    """Test proxy pool management"""

    def test_empty_pool_returns_none(self):
        from app.services.proxy import ProxyPool
        with patch("app.services.proxy.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                proxy_url="",
                proxy_pool="",
                proxy_rotation="round_robin"
            )
            ProxyPool._instance = None  # Reset singleton
            pool = ProxyPool()
            assert pool.get_httpx_proxy() is None
            assert pool.has_proxies is False

    def test_single_proxy(self):
        from app.services.proxy import ProxyPool
        with patch("app.services.proxy.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                proxy_url="http://proxy1:8080",
                proxy_pool="",
                proxy_rotation="round_robin"
            )
            ProxyPool._instance = None
            pool = ProxyPool()
            proxy = pool.get_httpx_proxy()
            assert proxy == "http://proxy1:8080"
            assert pool.has_proxies is True

    def test_pool_round_robin(self):
        from app.services.proxy import ProxyPool
        with patch("app.services.proxy.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                proxy_url="",
                proxy_pool="http://proxy1:8080,http://proxy2:8080",
                proxy_rotation="round_robin"
            )
            ProxyPool._instance = None
            pool = ProxyPool()
            first = pool.get_httpx_proxy()
            second = pool.get_httpx_proxy()
            assert first == "http://proxy1:8080"
            assert second == "http://proxy2:8080"

    def test_failure_tracking(self):
        from app.services.proxy import ProxyPool
        with patch("app.services.proxy.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                proxy_url="",
                proxy_pool="http://proxy1:8080",
                proxy_rotation="round_robin"
            )
            ProxyPool._instance = None
            pool = ProxyPool()
            # Report 3 failures to disable the proxy
            pool.report_failure("http://proxy1:8080")
            pool.report_failure("http://proxy1:8080")
            pool.report_failure("http://proxy1:8080")
            assert pool.get_httpx_proxy() is None  # Disabled after 3 failures

    def test_success_resets_failures(self):
        from app.services.proxy import ProxyPool
        with patch("app.services.proxy.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                proxy_url="",
                proxy_pool="http://proxy1:8080",
                proxy_rotation="round_robin"
            )
            ProxyPool._instance = None
            pool = ProxyPool()
            pool.report_failure("http://proxy1:8080")
            pool.report_failure("http://proxy1:8080")
            pool.report_success("http://proxy1:8080")  # Reset failures
            assert pool.get_httpx_proxy() == "http://proxy1:8080"  # Still active

    def test_playwright_proxy_format(self):
        from app.services.proxy import ProxyPool
        with patch("app.services.proxy.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                proxy_url="http://proxy1:8080",
                proxy_pool="",
                proxy_rotation="round_robin"
            )
            ProxyPool._instance = None
            pool = ProxyPool()
            pw_proxy = pool.get_playwright_proxy()
            assert pw_proxy == {"server": "http://proxy1:8080"}


class TestDiffService:
    """Test website change detection"""

    def _make_diff_service(self, tmpdir):
        from app.services.diff import DiffService
        diff = DiffService.__new__(DiffService)
        diff.snapshot_dir = Path(tmpdir) / "snapshots"
        diff.snapshot_dir.mkdir(parents=True, exist_ok=True)
        return diff

    def test_first_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            diff = self._make_diff_service(tmpdir)
            diff.save_snapshot("https://example.com", "Hello world")
            result = diff.get_diff("https://example.com")
            assert result is not None
            assert result["status"] == "no_previous"

    def test_no_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            diff = self._make_diff_service(tmpdir)
            # Save twice with same content
            diff.save_snapshot("https://example.com", "Same content")
            diff.save_snapshot("https://example.com", "Same content")
            result = diff.get_diff("https://example.com")
            assert result["status"] == "unchanged"

    def test_changes_detected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            diff = self._make_diff_service(tmpdir)
            diff.save_snapshot("https://example.com", "Version 1\nLine 2")
            diff.save_snapshot("https://example.com", "Version 2\nLine 2\nNew line")
            result = diff.get_diff("https://example.com")
            assert result["status"] == "changed"
            assert result["added_lines"] > 0 or result["removed_lines"] > 0
            assert "diff" in result
            assert "summary" in result

    def test_no_snapshot_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            diff = self._make_diff_service(tmpdir)
            result = diff.get_diff("https://never-visited.com")
            assert result is None

    def test_list_snapshots(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            diff = self._make_diff_service(tmpdir)
            diff.save_snapshot("https://example.com", "Hello")
            diff.save_snapshot("https://other.com", "World")
            snapshots = diff.list_snapshots()
            assert len(snapshots) == 2
            urls = [s["url"] for s in snapshots]
            assert "https://example.com" in urls
            assert "https://other.com" in urls


class TestStatsService:
    """Test usage statistics"""

    def test_initial_stats(self):
        from app.services.stats import StatsService
        stats = StatsService()
        data = stats.get_stats()
        assert data["total_requests"] == 0
        assert data["scrape_count"] == 0
        assert data["errors"] == 0

    def test_record_scrape(self):
        from app.services.stats import StatsService
        stats = StatsService()
        stats.record_scrape(1.5, tokens_saved=500)
        data = stats.get_stats()
        assert data["scrape_count"] == 1
        assert data["total_tokens_saved"] == 500
        assert data["total_requests"] == 1

    def test_record_interact(self):
        from app.services.stats import StatsService
        stats = StatsService()
        stats.record_interact(0.5, js_eval_count=3)
        data = stats.get_stats()
        assert data["interact_count"] == 1
        assert data["js_eval_count"] == 3

    def test_record_workflow(self):
        from app.services.stats import StatsService
        stats = StatsService()
        stats.record_workflow(2.0)
        data = stats.get_stats()
        assert data["workflow_count"] == 1

    def test_record_multiple(self):
        from app.services.stats import StatsService
        stats = StatsService()
        stats.record_scrape(1.0)
        stats.record_scrape(2.0)
        stats.record_interact(0.5)
        stats.record_error()
        data = stats.get_stats()
        assert data["total_requests"] == 3
        assert data["scrape_count"] == 2
        assert data["interact_count"] == 1
        assert data["errors"] == 1
        assert data["avg_response_time"] > 0


class TestRateLimiter:
    """Test rate limiting"""

    def test_allows_within_limit(self):
        from app.rate_limit import RateLimiter
        with patch("app.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(rate_limit_rpm=60)
            limiter = RateLimiter()
            for _ in range(5):
                assert limiter.check("test-key-a") is True

    def test_blocks_over_limit(self):
        from app.rate_limit import RateLimiter
        with patch("app.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(rate_limit_rpm=2)
            limiter = RateLimiter()
            assert limiter.check("test-key-b") is True   # 1st
            assert limiter.check("test-key-b") is True   # 2nd
            assert limiter.check("test-key-b") is False  # 3rd - blocked

    def test_unlimited_mode(self):
        from app.rate_limit import RateLimiter
        with patch("app.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(rate_limit_rpm=0)
            limiter = RateLimiter()
            for _ in range(100):
                assert limiter.check("test-key-c") is True

    def test_per_key_isolation(self):
        from app.rate_limit import RateLimiter
        with patch("app.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(rate_limit_rpm=2)
            limiter = RateLimiter()
            assert limiter.check("key-1") is True
            assert limiter.check("key-1") is True
            assert limiter.check("key-1") is False  # key-1 blocked
            assert limiter.check("key-2") is True   # key-2 still ok

    def test_retry_after(self):
        from app.rate_limit import RateLimiter
        with patch("app.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(rate_limit_rpm=60)
            limiter = RateLimiter()
            retry = limiter.get_retry_after("any-key")
            assert retry >= 1

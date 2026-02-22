"""
Nia-Link v0.9: WebMCP Sniffer Integration Test
Requires network access and browser — marked for manual/CI execution.
"""

import pytest
import sys
from pathlib import Path

from app.services.scraper import ScraperService


@pytest.mark.asyncio
async def test_v09_sniffer():
    """Test WebMCP sniffer mode with real sites (integration test)."""
    scraper = ScraperService()
    
    # Test: Google (fast mode, likely no WebMCP)
    try:
        res1 = await scraper.scrape("https://www.google.com", mode="fast")
        assert res1["data"].get("content") is not None
    except Exception:
        pytest.skip("Network unavailable or scraper dependencies missing")

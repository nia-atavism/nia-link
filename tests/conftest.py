"""
Nia-Link Test Configuration
"""

import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set test env vars BEFORE importing app modules
os.environ["API_KEYS"] = "test-key-123,test-key-456"
os.environ["RATE_LIMIT_RPM"] = "0"  # Disable rate limiting in tests
os.environ["DEBUG"] = "false"
os.environ["HEADLESS"] = "true"


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all singletons before each test"""
    from app.services.stats import StatsService
    from app.services.proxy import ProxyPool
    from app.services.queue import TaskQueue
    from app.services.session_manager import SessionManager
    
    StatsService._instance = None
    ProxyPool._instance = None
    TaskQueue._instance = None
    SessionManager._instance = None
    yield
    StatsService._instance = None
    ProxyPool._instance = None
    TaskQueue._instance = None
    SessionManager._instance = None


@pytest.fixture
def client():
    """FastAPI test client"""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Valid auth headers"""
    return {"Authorization": "Bearer test-key-123"}


@pytest.fixture
def invalid_auth_headers():
    """Invalid auth headers"""
    return {"Authorization": "Bearer wrong-key"}


@pytest.fixture
def mock_scraper_result():
    """Standard mock result from ScraperService.scrape()"""
    return {
        "data": {
            "title": "Test Page",
            "content": "# Test\n\nThis is test content.",
            "metadata": {
                "author": None,
                "published_date": None,
                "description": "A test page"
            },
            "links": ["https://example.com/link1"],
            "actions": [
                {
                    "type": "button",
                    "label": "Submit",
                    "selector": "#submit-btn",
                    "importance": "high"
                },
                {
                    "type": "input",
                    "label": "Search",
                    "selector": "#search-input",
                    "importance": "medium",
                    "placeholder": "Search..."
                }
            ]
        },
        "cost": {
            "original_size": 10000,
            "cleaned_size": 800,
            "reduction_percent": 92
        },
        "mode_used": "fast"
    }

"""
Nia-Link v0.9: Session Manager Tests
"""

import os
import json
import time
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ============================================================
# Unit Tests: SessionManager
# ============================================================

class TestSessionManager:
    """Test SessionManager service directly"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Reset singleton and use temp dir for each test"""
        from app.services.session_manager import SessionManager
        SessionManager._instance = None

        with patch("app.services.session_manager.get_settings") as mock_settings:
            settings = MagicMock()
            settings.get_session_dir.return_value = tmp_path / "sessions"
            mock_settings.return_value = settings
            self.mgr = SessionManager()
            self.tmp = tmp_path

    def test_create_session(self):
        meta = self.mgr.create("test-bot", description="My test session", ttl_hours=12)
        assert meta["session_id"] == "test-bot"
        assert meta["description"] == "My test session"
        assert meta["login_status"] == "new"
        assert meta["ttl_hours"] == 12
        assert meta["expires_at"] is not None

    def test_create_session_no_ttl(self):
        meta = self.mgr.create("no-expiry", ttl_hours=0)
        assert meta["expires_at"] is None

    def test_create_duplicate_returns_existing(self):
        meta1 = self.mgr.create("dup-test")
        meta2 = self.mgr.create("dup-test")
        assert meta1["created_at"] == meta2["created_at"]

    def test_get_session(self):
        self.mgr.create("get-test")
        meta = self.mgr.get("get-test")
        assert meta is not None
        assert meta["session_id"] == "get-test"

    def test_get_nonexistent(self):
        assert self.mgr.get("nope") is None

    def test_list_sessions(self):
        self.mgr.create("s1", description="First")
        self.mgr.create("s2", description="Second")
        sessions = self.mgr.list_sessions()
        assert len(sessions) == 2
        ids = [s["session_id"] for s in sessions]
        assert "s1" in ids
        assert "s2" in ids

    def test_list_empty(self):
        assert self.mgr.list_sessions() == []

    def test_delete_session(self):
        self.mgr.create("del-me")
        assert self.mgr.delete("del-me") is True
        assert self.mgr.get("del-me") is None

    def test_delete_nonexistent(self):
        assert self.mgr.delete("nope") is False

    def test_update_login_status(self):
        self.mgr.create("login-test")
        self.mgr.update_login_status(
            "login-test",
            login_url="https://example.com/login",
            status="logged_in",
            cookies_count=5
        )
        meta = self.mgr.get("login-test")
        assert meta["login_status"] == "logged_in"
        assert meta["login_url"] == "https://example.com/login"
        assert meta["cookies_count"] == 5

    def test_expired_session(self):
        meta = self.mgr.create("expire-test", ttl_hours=1)
        # Manually set expires_at to the past
        meta_path = self.mgr._meta_path("expire-test")
        with open(meta_path, "r") as f:
            data = json.load(f)
        data["expires_at"] = time.time() - 100
        with open(meta_path, "w") as f:
            json.dump(data, f)
        
        result = self.mgr.get("expire-test")
        assert result["login_status"] == "expired"

    def test_touch(self):
        self.mgr.create("touch-test")
        before = self.mgr.get("touch-test")["last_used"]
        time.sleep(0.05)
        self.mgr.touch("touch-test")
        after = self.mgr.get("touch-test")["last_used"]
        assert after >= before

    def test_cleanup_expired(self):
        self.mgr.create("keep-me", ttl_hours=24)
        self.mgr.create("expire-me", ttl_hours=1)
        # Expire one
        meta_path = self.mgr._meta_path("expire-me")
        with open(meta_path, "r") as f:
            data = json.load(f)
        data["expires_at"] = time.time() - 100
        with open(meta_path, "w") as f:
            json.dump(data, f)
        
        removed = self.mgr.cleanup_expired()
        assert removed == 1
        assert self.mgr.get("keep-me") is not None
        assert self.mgr.get("expire-me") is None

    def test_storage_state_paths(self):
        self.mgr.create("path-test")
        # No state file yet
        assert self.mgr.get_storage_state_path("path-test") is None
        # Save path always returns
        save_path = self.mgr.get_state_save_path("path-test")
        assert save_path.endswith(".json")


# ============================================================
# API Tests: Session Endpoints
# ============================================================

class TestSessionAPI:
    """Test session REST endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        # Reset singletons
        from app.services.session_manager import SessionManager
        from app.services.stats import StatsService
        from app.services.proxy import ProxyPool
        from app.services.queue import TaskQueue
        SessionManager._instance = None
        StatsService._instance = None
        ProxyPool._instance = None
        TaskQueue._instance = None

        os.environ["API_KEYS"] = "test-key"
        os.environ["SESSION_DIR"] = str(tmp_path / "sessions")

        from app.config import get_settings
        get_settings.cache_clear()
        from app.main import app
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer test-key"}

    def test_create_session(self):
        resp = self.client.post("/v1/session/create", json={
            "session_id": "api-test",
            "description": "Test session",
            "ttl_hours": 12
        }, headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "api-test"
        assert data["login_status"] == "new"

    def test_create_session_no_auth(self):
        resp = self.client.post("/v1/session/create", json={
            "session_id": "fail"
        })
        assert resp.status_code == 401

    def test_list_sessions_empty(self):
        resp = self.client.get("/v1/session/list", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 0

    def test_delete_session(self):
        # Create first
        self.client.post("/v1/session/create", json={
            "session_id": "to-delete"
        }, headers=self.headers)
        # Delete
        resp = self.client.delete("/v1/session/to-delete", headers=self.headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    def test_delete_nonexistent(self):
        resp = self.client.delete("/v1/session/nope-404", headers=self.headers)
        assert resp.status_code == 404

    def test_session_create_validation(self):
        # Empty session_id
        resp = self.client.post("/v1/session/create", json={
            "session_id": ""
        }, headers=self.headers)
        assert resp.status_code == 422  # Pydantic validation error

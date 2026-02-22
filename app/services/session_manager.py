"""
Nia-Link Session Manager v0.9
AI Agent session lifecycle management — create, login, persist, and destroy browser sessions.
"""

import json
import time
import logging
import hashlib
import threading
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timezone

from ..config import get_settings

logger = logging.getLogger("nia-link.session")


class SessionManager:
    """
    Manages named browser sessions for AI agents.
    
    Sessions persist Playwright storage_state (cookies + localStorage)
    so that login states survive across requests.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        settings = get_settings()
        self._session_dir = settings.get_session_dir()
        self._meta_dir = self._session_dir / "_meta"
        self._meta_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Session manager initialized: {self._session_dir}")
    
    def _meta_path(self, session_id: str) -> Path:
        """Get metadata file path for a session"""
        safe_id = hashlib.md5(session_id.encode()).hexdigest()[:12]
        return self._meta_dir / f"{safe_id}.json"
    
    def _state_path(self, session_id: str) -> Path:
        """Get Playwright storage state file path"""
        safe_id = hashlib.md5(session_id.encode()).hexdigest()[:12]
        return self._session_dir / f"session_{safe_id}.json"
    
    def create(self, session_id: str, description: str = "", ttl_hours: int = 24) -> Dict:
        """
        Create a new named session.
        
        Args:
            session_id: Unique session name (e.g. "github-bot", "amazon-checkout")
            description: Human-readable description
            ttl_hours: Time-to-live in hours (0 = no expiry)
        
        Returns:
            Session metadata dict
        """
        meta_path = self._meta_path(session_id)
        
        if meta_path.exists():
            # Session already exists — return its metadata
            return self._load_meta(session_id)
        
        meta = {
            "session_id": session_id,
            "description": description,
            "created_at": time.time(),
            "last_used": time.time(),
            "ttl_hours": ttl_hours,
            "expires_at": time.time() + (ttl_hours * 3600) if ttl_hours > 0 else None,
            "login_url": None,
            "login_status": "new",  # new | logged_in | expired
            "cookies_count": 0,
            "state_file": str(self._state_path(session_id))
        }
        
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Session created: {session_id}")
        return meta
    
    def get(self, session_id: str) -> Optional[Dict]:
        """Get session metadata, or None if not found"""
        meta = self._load_meta(session_id)
        if meta and self._is_expired(meta):
            meta["login_status"] = "expired"
        return meta
    
    def list_sessions(self) -> List[Dict]:
        """List all sessions with their metadata"""
        sessions = []
        if not self._meta_dir.exists():
            return sessions
        
        for meta_file in self._meta_dir.glob("*.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                # Check expiry
                if self._is_expired(meta):
                    meta["login_status"] = "expired"
                # Check if state file exists (has login data)
                state_path = Path(meta.get("state_file", ""))
                meta["has_state"] = state_path.exists()
                sessions.append(meta)
            except Exception as e:
                logger.warning(f"Failed to load session meta {meta_file}: {e}")
        
        # Sort by last_used descending
        sessions.sort(key=lambda s: s.get("last_used", 0), reverse=True)
        return sessions
    
    def update_login_status(self, session_id: str, login_url: str = None, 
                           status: str = "logged_in", cookies_count: int = 0):
        """Update session login status after a login action"""
        meta = self._load_meta(session_id)
        if not meta:
            return
        
        meta["last_used"] = time.time()
        if login_url:
            meta["login_url"] = login_url
        meta["login_status"] = status
        meta["cookies_count"] = cookies_count
        
        # Refresh TTL
        if meta.get("ttl_hours", 0) > 0:
            meta["expires_at"] = time.time() + (meta["ttl_hours"] * 3600)
        
        meta_path = self._meta_path(session_id)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    
    def touch(self, session_id: str):
        """Update last_used timestamp"""
        meta = self._load_meta(session_id)
        if not meta:
            return
        meta["last_used"] = time.time()
        meta_path = self._meta_path(session_id)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    
    def delete(self, session_id: str) -> bool:
        """Delete a session and its storage state"""
        meta_path = self._meta_path(session_id)
        state_path = self._state_path(session_id)
        
        deleted = False
        if meta_path.exists():
            meta_path.unlink()
            deleted = True
        if state_path.exists():
            state_path.unlink()
            deleted = True
        
        if deleted:
            logger.info(f"Session deleted: {session_id}")
        return deleted
    
    def get_storage_state_path(self, session_id: str) -> Optional[str]:
        """Get the Playwright storage state path if it exists"""
        state_path = self._state_path(session_id)
        if state_path.exists():
            return str(state_path)
        return None
    
    def get_state_save_path(self, session_id: str) -> str:
        """Get the path where Playwright should save storage state"""
        return str(self._state_path(session_id))
    
    def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        removed = 0
        for meta_file in self._meta_dir.glob("*.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                if self._is_expired(meta):
                    session_id = meta.get("session_id", "")
                    self.delete(session_id)
                    removed += 1
            except Exception:
                pass
        return removed
    
    def _load_meta(self, session_id: str) -> Optional[Dict]:
        """Load session metadata from disk"""
        meta_path = self._meta_path(session_id)
        if not meta_path.exists():
            return None
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    
    def _is_expired(self, meta: Dict) -> bool:
        """Check if a session has expired"""
        expires_at = meta.get("expires_at")
        if expires_at is None:
            return False  # No TTL = never expires
        return time.time() > expires_at

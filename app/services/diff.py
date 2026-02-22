"""
Nia-Link Diff Service v0.8
網站變更偵測 - 比對前後快照差異
"""

import hashlib
import json
import logging
import difflib
from typing import Optional, Dict, List
from pathlib import Path

from ..config import get_settings

logger = logging.getLogger("nia-link.diff")


class DiffService:
    """
    網站變更偵測服務
    
    功能：
    - 儲存頁面內容快照
    - 比對兩次爬取的差異
    - 回傳 unified diff + 變更摘要
    """
    
    def __init__(self):
        settings = get_settings()
        self.snapshot_dir = settings.get_registry_dir() / "snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    def _url_to_key(self, url: str) -> str:
        """URL 轉為檔案安全的 key"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_snapshot_path(self, url: str) -> Path:
        return self.snapshot_dir / f"{self._url_to_key(url)}.json"
    
    def save_snapshot(self, url: str, content: str, title: str = ""):
        """儲存頁面快照"""
        snapshot_path = self._get_snapshot_path(url)
        
        # 讀取現有快照（如果有的話，保存為 previous）
        existing = None
        if snapshot_path.exists():
            try:
                with open(snapshot_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                pass
        
        import time
        snapshot = {
            "url": url,
            "title": title,
            "content": content,
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
            "timestamp": time.time(),
            "previous": existing
        }
        
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Snapshot saved for {url}")
    
    def get_diff(self, url: str) -> Optional[Dict]:
        """
        比對當前快照與上次快照的差異
        
        Returns:
            包含 diff 和摘要的字典，或 None（無歷史快照）
        """
        snapshot_path = self._get_snapshot_path(url)
        if not snapshot_path.exists():
            return None
        
        try:
            with open(snapshot_path, "r", encoding="utf-8") as f:
                current = json.load(f)
        except Exception:
            return None
        
        previous = current.get("previous")
        if not previous:
            return {
                "status": "no_previous",
                "message": "No previous snapshot to compare",
                "url": url
            }
        
        # 比較 hash 快速判斷是否有變化
        if current["content_hash"] == previous["content_hash"]:
            return {
                "status": "unchanged",
                "message": "No changes detected",
                "url": url,
                "last_checked": current["timestamp"]
            }
        
        # 產生 unified diff
        old_lines = previous["content"].splitlines(keepends=True)
        new_lines = current["content"].splitlines(keepends=True)
        
        diff_lines = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"Previous ({previous.get('title', 'unknown')})",
            tofile=f"Current ({current.get('title', 'unknown')})",
            lineterm=""
        ))
        
        # 統計變更
        added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
        
        return {
            "status": "changed",
            "url": url,
            "added_lines": added,
            "removed_lines": removed,
            "diff": "\n".join(diff_lines),
            "previous_timestamp": previous.get("timestamp"),
            "current_timestamp": current.get("timestamp"),
            "summary": f"{added} lines added, {removed} lines removed"
        }
    
    def list_snapshots(self) -> List[Dict]:
        """列出所有快照"""
        snapshots = []
        for path in self.snapshot_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                snapshots.append({
                    "url": data.get("url"),
                    "title": data.get("title"),
                    "timestamp": data.get("timestamp"),
                    "has_previous": data.get("previous") is not None
                })
            except Exception:
                continue
        return snapshots

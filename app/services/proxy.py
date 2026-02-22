"""
Nia-Link Proxy Pool v0.9
代理池管理 - 支援多代理輪換（round_robin / random）
"""

import random as _random
import logging
import threading
from typing import Optional, List, Dict

from ..config import get_settings

logger = logging.getLogger("nia-link.proxy")


class ProxyPool:
    """
    代理池管理器（單例）
    
    支援：
    - HTTP / SOCKS5 代理
    - round_robin / random 輪換策略
    - 失敗自動標記與跳過
    - 健康檢查回復
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
        self._strategy = settings.proxy_rotation
        self._index = 0
        
        # 解析代理池
        self._proxies: List[Dict] = []
        
        # 優先使用 proxy_pool，其次使用單一 proxy_url
        pool_str = settings.proxy_pool
        if pool_str:
            for url in pool_str.split(","):
                url = url.strip()
                if url:
                    self._proxies.append({
                        "url": url,
                        "failures": 0,
                        "disabled": False
                    })
        elif settings.proxy_url:
            self._proxies.append({
                "url": settings.proxy_url,
                "failures": 0,
                "disabled": False
            })
        
        if self._proxies:
            logger.info(f"Proxy pool initialized: {len(self._proxies)} proxies, strategy={self._strategy}")
        else:
            logger.info("No proxies configured, using direct connection")
    
    @property
    def has_proxies(self) -> bool:
        return len(self._get_active()) > 0
    
    def _get_active(self) -> List[Dict]:
        """取得所有未停用的代理"""
        return [p for p in self._proxies if not p["disabled"]]
    
    def get_next(self) -> Optional[str]:
        """
        取得下一個代理 URL
        
        Returns:
            代理 URL 字串，或 None（無代理可用）
        """
        active = self._get_active()
        if not active:
            return None
        
        if self._strategy == "random":
            proxy = _random.choice(active)
        else:  # round_robin
            self._index = self._index % len(active)
            proxy = active[self._index]
            self._index += 1
        
        return proxy["url"]
    
    def get_playwright_proxy(self) -> Optional[dict]:
        """取得 Playwright 格式的代理設定"""
        url = self.get_next()
        if url:
            return {"server": url}
        return None
    
    def get_httpx_proxy(self) -> Optional[str]:
        """取得 httpx 格式的代理設定"""
        return self.get_next()
    
    def report_failure(self, proxy_url: str):
        """回報代理失敗，累積 3 次自動停用"""
        for p in self._proxies:
            if p["url"] == proxy_url:
                p["failures"] += 1
                if p["failures"] >= 3:
                    p["disabled"] = True
                    logger.warning(f"Proxy disabled after 3 failures: {proxy_url}")
                else:
                    logger.info(f"Proxy failure #{p['failures']}: {proxy_url}")
                break
    
    def report_success(self, proxy_url: str):
        """回報代理成功，重置失敗計數"""
        for p in self._proxies:
            if p["url"] == proxy_url:
                p["failures"] = 0
                break
    
    def reset_all(self):
        """重置所有代理狀態"""
        for p in self._proxies:
            p["failures"] = 0
            p["disabled"] = False
        self._index = 0
    
    def get_status(self) -> Dict:
        """取得代理池狀態"""
        return {
            "total": len(self._proxies),
            "active": len(self._get_active()),
            "disabled": len(self._proxies) - len(self._get_active()),
            "strategy": self._strategy,
            "proxies": [
                {
                    "url": p["url"][:20] + "...",  # 隱藏完整 URL
                    "failures": p["failures"],
                    "disabled": p["disabled"]
                }
                for p in self._proxies
            ]
        }

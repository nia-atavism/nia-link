"""
Nia-Link Stats Service v0.8
使用量統計追蹤
"""

import time
import threading
from typing import Dict


class StatsService:
    """記憶體內的使用量統計服務"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """單例模式"""
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
        self.start_time = time.time()
        self.scrape_count = 0
        self.interact_count = 0
        self.workflow_count = 0
        self.total_tokens_saved = 0
        self.total_response_time = 0.0
        self.captcha_detected_count = 0
        self.screenshot_count = 0
        self.js_eval_count = 0
        self.errors = 0
    
    def record_scrape(self, response_time: float, tokens_saved: int = 0, had_screenshot: bool = False):
        self.scrape_count += 1
        self.total_response_time += response_time
        self.total_tokens_saved += tokens_saved
        if had_screenshot:
            self.screenshot_count += 1
    
    def record_interact(self, response_time: float, js_eval_count: int = 0):
        self.interact_count += 1
        self.total_response_time += response_time
        self.js_eval_count += js_eval_count
    
    def record_workflow(self, response_time: float):
        self.workflow_count += 1
        self.total_response_time += response_time
    
    def record_captcha(self):
        self.captcha_detected_count += 1
    
    def record_error(self):
        self.errors += 1
    
    def get_stats(self) -> Dict:
        total_requests = self.scrape_count + self.interact_count + self.workflow_count
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": round(uptime, 1),
            "total_requests": total_requests,
            "scrape_count": self.scrape_count,
            "interact_count": self.interact_count,
            "workflow_count": self.workflow_count,
            "screenshot_count": self.screenshot_count,
            "js_eval_count": self.js_eval_count,
            "captcha_detected": self.captcha_detected_count,
            "errors": self.errors,
            "total_tokens_saved": self.total_tokens_saved,
            "avg_response_time": round(self.total_response_time / max(total_requests, 1), 3),
        }

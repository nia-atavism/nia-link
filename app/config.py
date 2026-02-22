"""
Nia-Link Configuration
配置管理模組
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


# 專案根目錄自動偵測
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """應用程式配置"""
    
    # 應用程式資訊
    app_name: str = "Nia-Link"
    app_version: str = "0.9.0"
    debug: bool = False
    
    # API 認證
    api_keys: str = "test-api-key"  # 逗號分隔的多個 API Keys
    
    # 爬蟲設定
    scraper_timeout: int = 30  # 秒
    scraper_wait_after_load: int = 2  # 頁面載入後等待時間（秒）
    max_content_length: int = 2000000  # 最大內容長度（字元）
    
    # 瀏覽器設定
    headless: bool = True
    browser_type: str = "chromium"  # chromium, firefox, webkit
    
    # 路徑設定（跨平台安全）
    registry_dir: str = ""  # 空字串 = 使用預設路徑（專案根目錄/registry）
    temp_dir: str = ""      # 空字串 = 使用預設路徑（專案根目錄/tmp）
    session_dir: str = ""   # 空字串 = 使用預設路徑（registry/sessions）
    
    # Proxy 設定
    proxy_url: str = ""  # 單一代理，例如 "http://user:pass@proxy:8080"
    proxy_pool: str = ""  # 逗號分隔的多代理 URL
    proxy_rotation: str = "round_robin"  # round_robin / random
    
    # Concurrency & Retry
    max_concurrency: int = 10
    max_retries: int = 3
    retry_base_delay: float = 1.0
    
    # Rate Limiting
    rate_limit_rpm: int = 60  # Requests per minute per API key (0 = unlimited)
    
    # CORS
    cors_origins: str = "*"  # Comma-separated allowed origins, e.g. "https://app.example.com,https://dashboard.example.com"
    
    # 任務佇列
    queue_max_size: int = 100
    
    # CAPTCHA 解決
    captcha_provider: str = ""  # "2captcha" / "anticaptcha" / ""
    captcha_api_key: str = ""
    
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    def get_registry_dir(self) -> Path:
        """取得 Registry 目錄路徑"""
        p = Path(self.registry_dir) if self.registry_dir else _PROJECT_ROOT / "registry"
        p.mkdir(parents=True, exist_ok=True)
        return p
    
    def get_temp_dir(self) -> Path:
        """取得暫存目錄路徑"""
        p = Path(self.temp_dir) if self.temp_dir else _PROJECT_ROOT / "tmp"
        p.mkdir(parents=True, exist_ok=True)
        return p
    
    def get_session_dir(self) -> Path:
        """取得 Session 目錄路徑"""
        p = Path(self.session_dir) if self.session_dir else self.get_registry_dir() / "sessions"
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache()
def get_settings() -> Settings:
    """獲取快取的配置實例"""
    return Settings()

"""
Nia-Link Scraper Service v0.9
網頁爬蟲核心服務 - 混合引擎 (Hybrid Engine)
"""

import asyncio
import time
import json
import base64
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

from ..config import get_settings
from ..schemas import OutputFormat, ErrorCode, ScrapeMode
from .cleaner import CleanerService
from .extractor import ActionExtractor, TokenCalculator
from .proxy import ProxyPool

logger = logging.getLogger("nia-link.scraper")


class ScraperError(Exception):
    """爬蟲錯誤基類"""
    def __init__(self, code: ErrorCode, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ScraperService:
    """
    網頁爬蟲服務 - 混合引擎
    
    Level 1 (fast): 使用 httpx 進行快速 HTTP 請求
    Level 2 (visual): 使用 Crawl4AI 無頭瀏覽器（需 JavaScript）
    
    特殊支援：
    - GitHub: 自動嘗試獲取 raw README 內容
    - 新聞網站: 智慧內容提取
    """
    
    # 常見瀏覽器 User-Agent
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # GitHub README 的常見檔案名
    GITHUB_README_FILES = ['README.md', 'readme.md', 'README.MD', 'README', 'readme']
    
    # v0.4: 彈窗自動關閉腳本
    POPUP_DISMISS_SCRIPT = """
    () => {
        // 常見關閉按鈕選擇器
        const closeSelectors = [
            '[aria-label="Close"]',
            '[aria-label="close"]',
            '[data-testid="close"]',
            '[data-testid="xMigrationBottomBar"]',
            '.modal-close',
            '.popup-close',
            '[class*="dismiss"]',
            '[class*="close-button"]',
            '[class*="CloseButton"]',
            'button[aria-label*="close"]',
            'button[aria-label*="Close"]',
            '[role="button"][aria-label*="close"]',
            // Twitter/X 特定
            '[data-testid="app-bar-close"]',
            '[aria-label="Close dialog"]',
            // Threads 特定
            '[aria-label="Dismiss"]',
            // Reddit 特定
            'button.close-button',
            '[data-testid="close-button"]'
        ];
        let dismissed = 0;
        closeSelectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                try { el.click(); dismissed++; } catch(e) {}
            });
        });
        // 移除遮罩層
        document.querySelectorAll('[class*="overlay"], [class*="modal-backdrop"], [class*="Overlay"]')
            .forEach(el => { try { el.remove(); dismissed++; } catch(e) {} });
        // 移除 body 滾動鎖定
        document.body.style.overflow = 'auto';
        return dismissed;
    }
    """

    # =============== v0.9: WebMCP 混合動力支持 ===============
    # 探測腳本：檢查瀏覽器是否支援原生 WebMCP (navigator.modelContext)
    WEBMCP_SNIFFER_SCRIPT = """
    () => {
        return {
            supported: !!(window.navigator && window.navigator.modelContext),
            version: window.navigator?.modelContext?.version || "unknown",
            capabilities: window.navigator?.modelContext?.capabilities || []
        };
    }
    """
    
    def __init__(self):
        """初始化爬蟲服務"""
        self.settings = get_settings()
        self.cleaner = CleanerService()
        self.extractor = ActionExtractor()
        self.token_calc = TokenCalculator()
        self.proxy_pool = ProxyPool()
        self.registry_path = self.settings.get_registry_dir() / "action_maps.json"
        self._semaphore = asyncio.Semaphore(self.settings.max_concurrency)
        self._init_registry()

    def _init_registry(self):
        """初始化行動地圖註冊表"""
        if not self.registry_path.exists():
            self.registry_path.write_text(json.dumps({}))

    def _get_cached_map(self, url: str) -> Optional[dict]:
        """從註冊表獲取緩存的行動地圖"""
        try:
            data = json.loads(self.registry_path.read_text())
            key = urlparse(url).netloc
            cached = data.get(key)
            if cached:
                # 快取 TTL：1 小時
                if time.time() - cached.get("timestamp", 0) < 3600:
                    return cached
            return None
        except Exception:
            return None

    def _save_to_registry(self, url: str, result: dict):
        """將抓取結果存入註冊表"""
        try:
            data = json.loads(self.registry_path.read_text())
            key = urlparse(url).netloc
            data[key] = {
                "timestamp": time.time(),
                "title": result["data"]["title"],
                "actions": result["data"]["actions"],
                "metadata": result["data"]["metadata"],
                "cost": result.get("cost") # 👈 關鍵：補存成本資訊
            }
            self.registry_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning(f"Registry save failed: {e}")

    async def _retry_with_backoff(self, coro_func, *args, **kwargs):
        """
        指數退避重試包裝器
        """
        last_exception = None
        for attempt in range(self.settings.max_retries):
            try:
                return await coro_func(*args, **kwargs)
            except ScraperError as e:
                # 不重試客戶端錯誤
                if e.code in (ErrorCode.INVALID_URL, ErrorCode.CONTENT_TOO_LARGE):
                    raise
                last_exception = e
                delay = self.settings.retry_base_delay * (2 ** attempt)
                logger.info(f"Retry {attempt + 1}/{self.settings.max_retries} after {delay:.1f}s: {e.message}")
                await asyncio.sleep(delay)
        raise last_exception

    # =============== v0.9: CAPTCHA 偵測 ===============

    CAPTCHA_MARKERS = [
        'g-recaptcha', 'grecaptcha', 'recaptcha',
        'h-captcha', 'hcaptcha',
        'cf-turnstile', 'cf-challenge',
        'challenge-form', 'challenge-running',
        'verify you are human', 'verify you\'re human',
        'please verify', 'are you a robot',
        'captcha-container', 'captcha_container',
    ]

    def _detect_captcha(self, html_content: str) -> Optional[str]:
        """偵測頁面是否包含 CAPTCHA 挑戰"""
        html_lower = html_content.lower()
        for marker in self.CAPTCHA_MARKERS:
            if marker in html_lower:
                # 判斷類型
                if 'recaptcha' in marker or 'grecaptcha' in marker:
                    return 'reCAPTCHA'
                elif 'hcaptcha' in marker or 'h-captcha' in marker:
                    return 'hCaptcha'
                elif 'turnstile' in marker or 'cf-challenge' in marker:
                    return 'Cloudflare Turnstile'
                else:
                    return 'Generic CAPTCHA'
        return None

    # =============== v0.9: 截圖支援 ===============

    async def _take_screenshot(self, url: str, timeout: int = 30) -> Optional[str]:
        """使用 Playwright 截取頁面截圖，回傳 Base64 編碼"""
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                launch_opts = {"headless": True}
                # 代理池支援
                proxy_config = self.proxy_pool.get_playwright_proxy()
                if proxy_config:
                    launch_opts["proxy"] = proxy_config
                # 多瀏覽器引擎支援
                browser_type_name = self.settings.browser_type
                browser_engine = getattr(p, browser_type_name, p.chromium)
                browser = await browser_engine.launch(**launch_opts)
                page = await browser.new_page(viewport={"width": 1280, "height": 720})
                await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
                screenshot_bytes = await page.screenshot(type="png", full_page=False)
                await browser.close()
                return base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception as e:
            logger.warning(f"Screenshot failed: {e}")
            return None

    # =============== v0.9: CAPTCHA 解決策略 ===============

    async def _solve_captcha(self, url: str, captcha_type: str) -> bool:
        """
        嘗試使用第三方服務解決 CAPTCHA
        
        Returns:
            True = 解決成功（重新爬取），False = 無法解決
        """
        provider = self.settings.captcha_provider
        api_key = self.settings.captcha_api_key
        
        if not provider or not api_key:
            logger.info(f"No CAPTCHA solver configured, cannot solve {captcha_type}")
            return False
        
        try:
            if provider == "2captcha":
                # 2Captcha API 預留接口
                logger.info(f"Attempting to solve {captcha_type} via 2Captcha...")
                async with httpx.AsyncClient(timeout=120) as client:
                    # 步驟 1: 提交 CAPTCHA
                    submit_resp = await client.post(
                        "http://2captcha.com/in.php",
                        data={
                            "key": api_key,
                            "method": "userrecaptcha",
                            "googlekey": "",  # 需要從頁面中提取 sitekey
                            "pageurl": url,
                            "json": 1
                        }
                    )
                    result = submit_resp.json()
                    if result.get("status") != 1:
                        logger.warning(f"2Captcha submit failed: {result}")
                        return False
                    
                    task_id = result["request"]
                    
                    # 步驟 2: 輪詢結果
                    for _ in range(30):  # 最多等 150 秒
                        await asyncio.sleep(5)
                        poll_resp = await client.get(
                            f"http://2captcha.com/res.php?key={api_key}&action=get&id={task_id}&json=1"
                        )
                        poll_result = poll_resp.json()
                        if poll_result.get("status") == 1:
                            logger.info(f"CAPTCHA solved successfully")
                            return True
                        elif "CAPCHA_NOT_READY" not in str(poll_result.get("request", "")):
                            logger.warning(f"2Captcha failed: {poll_result}")
                            return False
                    
                    logger.warning("2Captcha timeout")
                    return False
            
            elif provider == "anticaptcha":
                logger.info(f"AntiCaptcha provider configured but not yet implemented")
                return False
            
            else:
                logger.warning(f"Unknown CAPTCHA provider: {provider}")
                return False
                
        except Exception as e:
            logger.error(f"CAPTCHA solving error: {e}")
            return False
    
    def _is_github_repo(self, url: str) -> bool:
        """檢查是否為 GitHub 倉庫頁面"""
        parsed = urlparse(url)
        if 'github.com' not in parsed.netloc:
            return False
        # 路徑格式: /owner/repo 或 /owner/repo/...
        path_parts = [p for p in parsed.path.split('/') if p]
        return len(path_parts) >= 2
    
    # =============== v0.4: YouTube 特殊處理 ===============
    
    def _is_youtube_url(self, url: str) -> bool:
        """檢查是否為 YouTube URL"""
        parsed = urlparse(url)
        return 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc
    
    def _extract_youtube_video_id(self, url: str) -> Optional[str]:
        """從 URL 提取 YouTube 影片 ID"""
        import re
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11})(?:[&?/]|$)',
            r'youtu\.be/([0-9A-Za-z_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def _fetch_youtube_info(self, url: str, output_format: OutputFormat) -> Optional[dict]:
        """
        使用 yt-dlp 提取 YouTube 影片資訊
        返回標準化的 scrape 回應格式
        """
        try:
            import yt_dlp
        except ImportError:
            return None
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'writesubtitles': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                # 建構 Markdown 內容
                title = info.get('title', 'Untitled Video')
                channel = info.get('channel', info.get('uploader', 'Unknown'))
                description = info.get('description', '')
                duration = info.get('duration', 0)
                view_count = info.get('view_count', 0)
                upload_date = info.get('upload_date', '')
                
                # 格式化時長
                if duration:
                    mins, secs = divmod(duration, 60)
                    hours, mins = divmod(mins, 60)
                    if hours:
                        duration_str = f"{hours}:{mins:02d}:{secs:02d}"
                    else:
                        duration_str = f"{mins}:{secs:02d}"
                else:
                    duration_str = "Unknown"
                
                # 建構 Markdown
                markdown_content = f"""# {title}

**頻道**: {channel}
**時長**: {duration_str}
**觀看次數**: {view_count:,}
**上傳日期**: {upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8] if len(upload_date) >= 8 else upload_date}

## 影片描述

{description[:2000] if description else '(無描述)'}
"""
                
                # 計算節省率
                original_size = len(description.encode('utf-8')) if description else 100
                cleaned_size = len(markdown_content.encode('utf-8'))
                cost_info = self.cleaner.calculate_savings(original_size * 10, cleaned_size)
                
                return {
                    'data': {
                        'title': title,
                        'content': markdown_content,
                        'metadata': {
                            'author': channel,
                            'published_date': upload_date,
                            'description': description[:200] if description else None,
                            'youtube_mode': True
                        },
                        'links': [url],
                        'actions': None
                    },
                    'cost': cost_info,
                    'mode_used': ScrapeMode.FAST
                }
                
        except Exception as e:
            logger.warning(f"YouTube extraction failed: {e}")
            return None
    
    def _get_github_raw_readme_url(self, url: str) -> Optional[str]:
        """獲取 GitHub README 的 raw URL"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) >= 2:
            owner, repo = path_parts[0], path_parts[1]
            # 嘗試 main 和 master 分支
            return f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
        return None
    
    async def _fetch_github_readme(self, url: str, timeout: int) -> Optional[str]:
        """嘗試獲取 GitHub README 的原始內容"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) < 2:
            return None
        
        owner, repo = path_parts[0], path_parts[1]
        branches = ['main', 'master', 'develop']
        
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            for branch in branches:
                for readme_file in self.GITHUB_README_FILES:
                    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{readme_file}"
                    try:
                        response = await client.get(raw_url)
                        if response.status_code == 200:
                            return response.text
                    except Exception:
                        continue
        return None
    
    def _build_github_response(self, url: str, readme_content: str, output_format: OutputFormat) -> dict:
        """建構 GitHub README 的標準回應格式"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        owner, repo = path_parts[0], path_parts[1]
        
        original_size = len(readme_content.encode('utf-8'))
        
        # 根據格式處理內容
        if output_format == OutputFormat.MARKDOWN:
            content = readme_content
        elif output_format == OutputFormat.TEXT:
            # 簡單移除 Markdown 符號
            import re
            content = re.sub(r'[#*`\[\]()]', '', readme_content)
            content = re.sub(r'\n{3,}', '\n\n', content)
        else:  # JSON
            content = {
                'readme': readme_content,
                'owner': owner,
                'repo': repo
            }
        
        if isinstance(content, dict):
            import json
            cleaned_size = len(json.dumps(content, ensure_ascii=False).encode('utf-8'))
        else:
            cleaned_size = len(content.encode('utf-8'))
        
        cost_info = self.cleaner.calculate_savings(original_size, cleaned_size)
        
        return {
            'data': {
                'title': f'{owner}/{repo} - README',
                'content': content,
                'metadata': {
                    'author': owner,
                    'published_date': None,
                    'description': f'GitHub repository: {owner}/{repo}'
                },
                'links': [url, f'https://github.com/{owner}/{repo}'],
                'actions': None
            },
            'cost': cost_info,
            'mode_used': ScrapeMode.FAST
        }
    
    async def scrape(
        self,
        url: str,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        mode: ScrapeMode = ScrapeMode.FAST,
        wait_for_selector: Optional[str] = None,
        timeout: Optional[int] = None,
        extract_actions: bool = True,
        cookies: Optional[dict] = None,
        use_cache: bool = True,
        screenshot: bool = False
    ) -> dict:
        """
        抓取並處理網頁內容（混合引擎）
        使用 Semaphore 限制併發數，支援指數退避重試
        """
        async with self._semaphore:
            return await self._retry_with_backoff(
                self._scrape_impl,
                url=url,
                output_format=output_format,
                mode=mode,
                wait_for_selector=wait_for_selector,
                timeout=timeout,
                extract_actions=extract_actions,
                cookies=cookies,
                use_cache=use_cache,
                screenshot=screenshot
            )

    async def _scrape_impl(
        self,
        url: str,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        mode: ScrapeMode = ScrapeMode.FAST,
        wait_for_selector: Optional[str] = None,
        timeout: Optional[int] = None,
        extract_actions: bool = True,
        cookies: Optional[dict] = None,
        use_cache: bool = True,
        screenshot: bool = False
    ) -> dict:
        """實際的抓取實作邏輯"""
        # 智能模式切換：針對特定高防禦或動態網域強制使用 VISUAL 模式
        target_mode = mode
        dynamic_domains = ["x.com", "twitter.com", "threads.net", "facebook.com", "instagram.com", "bilibili.com"]
        if any(domain in url.lower() for domain in dynamic_domains):
            if target_mode != ScrapeMode.VISUAL:
                logger.info(f"🛡️ 偵測到動態目標 {url}，自動切換至 VISUAL 模式以穿透防禦。")
                target_mode = ScrapeMode.VISUAL

        # 1. 檢查緩存 (Memory Center)
        if use_cache and not screenshot:
            cached = self._get_cached_map(url)
            if cached:
                logger.info(f"Cache hit for {urlparse(url).netloc}")
                # 判斷當初存入快取時是否為 Visual 模式
                is_visual = cached.get("metadata", {}).get("visual_mode", False)
                cached_mode = ScrapeMode.VISUAL if is_visual else ScrapeMode.FAST
                
                # 恢復快取中的 Token 節省資訊，若無則預設為 0
                cost_data = cached.get("cost", {"original_size": 0, "cleaned_size": 0, "tokens_saved": 0, "reduction_percent": 0})
                
                return {
                    "data": {
                        "title": cached.get("title", "Cached"),
                        "content": f"[Cached result for {urlparse(url).netloc}]",
                        "metadata": cached.get("metadata", {}),
                        "actions": cached.get("actions"),
                        "links": None
                    },
                    "cost": cost_data, # 👈 關鍵：回傳正確的節省數據
                    "mode_used": cached_mode, # 👈 動態回傳正確的模式
                    "from_registry": True
                }
        
        # 2. 驗證 URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ScraperError(
                code=ErrorCode.INVALID_URL,
                message="Invalid URL format",
                details={"url": url}
            )
        
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        effective_timeout = timeout or self.settings.scraper_timeout
        
        # 3. 根據模式選擇爬蟲策略
        # ⚠️ 強制校準：確保使用 target_mode 而非傳入的原始 mode
        if target_mode == ScrapeMode.VISUAL:
            logger.info(f"🔮 正在以 VISUAL 模式啟動無頭瀏覽器...")
            result = await self._scrape_visual(
                url=url,
                base_url=base_url,
                output_format=output_format,
                wait_for_selector=wait_for_selector,
                timeout=effective_timeout,
                extract_actions=extract_actions,
                cookies=cookies
            )
        else:
            result = await self._scrape_fast(
                url=url,
                base_url=base_url,
                output_format=output_format,
                timeout=effective_timeout,
                extract_actions=extract_actions,
                cookies=cookies
            )
        
        # 4. v0.9: CAPTCHA 偵測與解決
        content_str = str(result.get("data", {}).get("content", ""))
        captcha_type = self._detect_captcha(content_str)
        if captcha_type:
            logger.warning(f"CAPTCHA detected on {url}: {captcha_type}")
            # 嘗試解決
            solved = await self._solve_captcha(url, captcha_type)
            if not solved:
                raise ScraperError(
                    code=ErrorCode.CAPTCHA_DETECTED,
                    message=f"CAPTCHA challenge detected: {captcha_type}",
                    details={"url": url, "captcha_type": captcha_type, "solver_attempted": bool(self.settings.captcha_provider)}
                )
            logger.info(f"CAPTCHA solved for {url}, re-scraping recommended")
        
        # 5. v0.9: 可選截圖
        if screenshot:
            screenshot_b64 = await self._take_screenshot(url, effective_timeout)
            result["screenshot_base64"] = screenshot_b64
        
        # 6. 存入註冊表
        self._save_to_registry(url, result)
        return result
    
    async def _scrape_fast(
        self,
        url: str,
        base_url: str,
        output_format: OutputFormat,
        timeout: int,
        extract_actions: bool,
        cookies: Optional[dict] = None  # v0.4: Cookie 注入
    ) -> dict:
        """
        Level 1: 快速 HTTP 爬蟲模式
        使用 httpx 進行純 HTTP 請求，適用於靜態網頁
        
        特殊處理：
        - GitHub repo: 自動獲取 raw README 內容
        - YouTube: 使用 yt-dlp 獲取影片資訊
        """
        # GitHub 特殊處理：嘗試獲取 raw README
        if self._is_github_repo(url):
            readme_content = await self._fetch_github_readme(url, timeout)
            if readme_content:
                return self._build_github_response(url, readme_content, output_format)
        
        # v0.4: YouTube 特殊處理：使用 yt-dlp
        if self._is_youtube_url(url):
            youtube_result = await self._fetch_youtube_info(url, output_format)
            if youtube_result:
                return youtube_result
        
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        proxy_config = None # Initialize proxy_config
        try:
            # Use proxy pool for rotation
            proxy_config = self.proxy_pool.get_httpx_proxy()
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                headers=headers,
                cookies=cookies,
                proxy=proxy_config
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Report proxy success
                if proxy_config:
                    self.proxy_pool.report_success(proxy_config)
                
                html_content = response.text
                original_size = len(html_content.encode('utf-8'))
                
                # 檢查內容大小
                if original_size > self.settings.max_content_length:
                    raise ScraperError(
                        code=ErrorCode.CONTENT_TOO_LARGE,
                        message=f"Content exceeds maximum size ({self.settings.max_content_length} bytes)",
                        details={"size": original_size}
                    )
                
                # 提取元數據和連結
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'lxml')
                raw_soup = BeautifulSoup(html_content, 'lxml')
                
                metadata = self.cleaner.extract_metadata(soup)
                links = self.cleaner.extract_links(soup, base_url)
                
                # 提取可操作元件（行動地圖）- 使用 v0.2 extractor
                actions = None
                if extract_actions:
                    actions = self.extractor.extract_actions(html_content)
                
                # 根據格式轉換內容（傳遞 URL 以進行網站類型偵測）
                if output_format == OutputFormat.MARKDOWN:
                    content = self.cleaner.to_markdown(html_content, url=url)
                elif output_format == OutputFormat.JSON:
                    content = self.cleaner.to_json_structure(html_content)
                else:  # TEXT
                    content = self.cleaner.to_text(html_content)
                
                # 計算內容大小
                if isinstance(content, dict):
                    import json
                    cleaned_size = len(json.dumps(content, ensure_ascii=False).encode('utf-8'))
                else:
                    cleaned_size = len(content.encode('utf-8'))
                
                # 計算節省資訊
                cost_info = self.cleaner.calculate_savings(original_size, cleaned_size)
                
                # 確保 metadata 不是 None
                if metadata is None:
                    metadata = {}
                
                return {
                    'data': {
                        'title': metadata.get('title') or 'Untitled',
                        'content': content,
                        'metadata': {
                            'author': metadata.get('author'),
                            'published_date': metadata.get('published_date'),
                            'description': metadata.get('description')
                        },
                        'links': links,
                        'actions': actions
                    },
                    'cost': cost_info,
                    'mode_used': ScrapeMode.FAST
                }
                
        except httpx.TimeoutException:
            raise ScraperError(
                code=ErrorCode.TARGET_TIMEOUT,
                message="Target website took too long to respond",
                details={"url": url, "timeout": timeout}
            )
        except httpx.HTTPStatusError as e:
            raise ScraperError(
                code=ErrorCode.TARGET_UNREACHABLE,
                message=f"HTTP error: {e.response.status_code}",
                details={"url": url, "status_code": e.response.status_code}
            )
        except httpx.RequestError as e:
            raise ScraperError(
                code=ErrorCode.TARGET_UNREACHABLE,
                message=f"Failed to fetch URL: {str(e)}",
                details={"url": url}
            )
        except ScraperError:
            raise
        except Exception as e:
            raise ScraperError(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Internal scraping error: {str(e)}",
                details={"url": url, "error_type": type(e).__name__}
            )
    
    async def _scrape_visual(
        self,
        url: str,
        base_url: str,
        output_format: OutputFormat,
        wait_for_selector: Optional[str],
        timeout: int,
        extract_actions: bool,
        cookies: Optional[dict] = None  # v0.4: Cookie 注入
    ) -> dict:
        """
        Level 2: 視覺分析模式 (混合 WebMCP 支持)
        使用無頭瀏覽器進行完整渲染，並優先探測 WebMCP 支援。
        """
        crawler = None
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
            
            js_code = f"""
            (() => {{
                const dismissPopups = {self.POPUP_DISMISS_SCRIPT};
                const sniffer = {self.WEBMCP_SNIFFER_SCRIPT};
                
                dismissPopups();
                return sniffer();
            }})()
            """
            
            config_kwargs = {
                'js_code': js_code,
                'wait_until': "domcontentloaded",
                'delay_before_return_html': 2.0,
            }
            
            if cookies:
                cookie_list = [{"name": k, "value": v, "domain": ""} for k, v in cookies.items()]
                config_kwargs['cookies'] = cookie_list
            
            config = CrawlerRunConfig(**config_kwargs)
            
            # 【強化防護】加入明確的 crawler 變數初始化，不使用 async with 以便精確控制
            crawler = AsyncWebCrawler(always_bypass_cache=True)
            await crawler.start() # 強制手動啟動
            
            result = await asyncio.wait_for(
                crawler.arun(url, config=config),
                timeout=timeout + 10
            )
            
            if not result.success:
                raise ScraperError(
                    code=ErrorCode.TARGET_UNREACHABLE,
                    message=f"Failed to fetch URL: {getattr(result, 'error_message', 'Unknown error')}",
                    details={"url": url, "mode": "visual"}
                )
            
            # 提取 WebMCP 探測結果
            webmcp_info = getattr(result, 'js_execution_result', {}).get('value', {})
            if webmcp_info and webmcp_info.get('supported'):
                logger.info(f"[WebMCP] Native support detected on {urlparse(url).netloc} (v{webmcp_info.get('version')})")
            
            html_content = result.html
            original_size = len(html_content.encode('utf-8'))
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            
            metadata = self.cleaner.extract_metadata(soup)
            links = self.cleaner.extract_links(soup, base_url)
            
            actions = None
            if extract_actions:
                actions = self.extractor.extract_actions(html_content)
            
            if output_format == OutputFormat.MARKDOWN:
                content = self.cleaner.to_markdown(html_content, url=url)
            elif output_format == OutputFormat.JSON:
                content = self.cleaner.to_json_structure(html_content)
            else:
                content = self.cleaner.to_text(html_content)
            
            cleaned_size = len(json.dumps(content, ensure_ascii=False).encode('utf-8')) if isinstance(content, dict) else len(content.encode('utf-8'))
            cost_info = self.cleaner.calculate_savings(original_size, cleaned_size)
            
            return {
                'data': {
                    'title': metadata.get('title') or 'Untitled',
                    'content': content,
                    'metadata': {
                        'author': metadata.get('author'),
                        'published_date': metadata.get('published_date'),
                        'description': metadata.get('description'),
                        'visual_mode': True,
                        'webmcp_native': webmcp_info.get('supported', False) if webmcp_info else False,
                        'webmcp_version': webmcp_info.get('version') if webmcp_info else None
                    },
                    'links': links,
                    'actions': actions
                },
                'cost': cost_info,
                'mode_used': ScrapeMode.VISUAL
            }
                
        except ImportError:
            raise ScraperError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Visual mode requires Crawl4AI. Please install it or use mode='fast'",
                details={"url": url, "mode": "visual"}
            )
        except asyncio.TimeoutError:
            logger.error(f"⏳ Visual 模式執行超時: {url}")
            raise ScraperError(
                code=ErrorCode.TARGET_TIMEOUT,
                message="Target website took too long to respond (visual mode)",
                details={"url": url, "timeout": timeout, "mode": "visual"}
            )
        except ScraperError:
            raise
        except Exception as e:
            # 記錄真實死因，不再讓它無聲無息地降級
            logger.error(f"🚨 Visual 模式發生嚴重錯誤，準備降級: {str(e)}")
            try:
                return await self._scrape_fast(url=url, base_url=base_url, output_format=output_format, timeout=timeout, extract_actions=extract_actions, cookies=cookies)
            except Exception as fallback_e:
                raise ScraperError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=f"Visual mode failed ({str(e)}) and fallback also failed: {str(fallback_e)}",
                    details={"url": url, "mode": "visual"}
                )
        finally:
            # 【一擊必殺】：無論成功或失敗，強制砍掉這個 crawler 的所有背景進程
            if crawler:
                try:
                    logger.info("🧹 強制清理 Crawl4AI 資源...")
                    await crawler.close()
                except Exception as ce:
                    logger.warning(f"Error during crawler closure: {ce}")

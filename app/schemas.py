"""
Nia-Link v0.9 Schemas
Pydantic 資料模型定義
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


# ============================================================
# 列舉類型 (Enums)
# ============================================================

class OutputFormat(str, Enum):
    """輸出格式列舉"""
    MARKDOWN = "markdown"
    JSON = "json"
    TEXT = "text"


class ScrapeMode(str, Enum):
    """爬蟲模式列舉"""
    FAST = "fast"      # Level 1: DOM 爬蟲（快速模式）
    VISUAL = "visual"  # Level 2: 視覺分析（預留接口）


class ActionType(str, Enum):
    """可操作元件類型"""
    BUTTON = "button"
    INPUT = "input"
    LINK = "link"
    SELECT = "select"
    CHECKBOX = "checkbox"
    TEXTAREA = "textarea"


class Importance(str, Enum):
    """元件重要性評估"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================
# 請求模型 (Request Models)
# ============================================================

class ScrapeRequest(BaseModel):
    """
    爬蟲請求模型
    POST /v1/scrape 的請求體
    """
    url: HttpUrl = Field(
        ...,
        description="要爬取的目標網址",
        examples=["https://example.com"]
    )
    format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN,
        description="輸出格式: markdown, json, text"
    )
    mode: ScrapeMode = Field(
        default=ScrapeMode.FAST,
        description="爬蟲模式: fast (DOM爬蟲) 或 visual (視覺分析)"
    )
    wait_for_selector: Optional[str] = Field(
        default=None,
        description="等待特定 CSS 選擇器出現後才抓取"
    )
    timeout: Optional[int] = Field(
        default=None,
        ge=5,
        le=60,
        description="自訂超時時間（秒）"
    )
    extract_actions: bool = Field(
        default=True,
        description="是否提取可操作元件（行動地圖）"
    )
    # v0.4: Cookie 注入支援
    cookies: Optional[dict] = Field(
        default=None,
        description="Cookie 字典，用於已登入狀態抓取（例如 {'auth_token': 'xxx'}）"
    )
    # v0.9: 截圖支援
    screenshot: bool = Field(
        default=False,
        description="是否截取頁面截圖（自動升級為 visual 模式）"
    )


# ============================================================
# 回應模型 - v0.2 規格 (Response Models)
# ============================================================

class MetaInfo(BaseModel):
    """元數據資訊 - v0.2 核心賣點"""
    url: str = Field(description="原始請求 URL")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="處理時間戳"
    )
    token_savings: str = Field(
        description="Token 節省百分比 (例如 '92.5%')"
    )
    process_time: float = Field(
        description="處理時間（秒）"
    )
    mode_used: ScrapeMode = Field(
        default=ScrapeMode.FAST,
        description="實際使用的爬蟲模式"
    )


class ContentInfo(BaseModel):
    """內容資訊"""
    title: str = Field(description="頁面標題")
    markdown: str = Field(description="清洗後的 Markdown 內容")
    raw_text_length: int = Field(description="原始文字長度")
    description: Optional[str] = Field(
        default=None,
        description="頁面描述"
    )
    links: Optional[List[str]] = Field(
        default=None,
        description="頁面中的連結列表"
    )


class ActionItem(BaseModel):
    """
    可操作元件項目 - 行動地圖核心
    用於 AI Agent 執行自動化操作
    """
    type: ActionType = Field(description="元件類型")
    label: str = Field(description="元件標籤/文字")
    selector: str = Field(description="CSS 選擇器")
    importance: Importance = Field(
        default=Importance.MEDIUM,
        description="元件重要性"
    )
    value: Optional[str] = Field(
        default=None,
        description="當前值（用於 input/textarea）"
    )
    placeholder: Optional[str] = Field(
        default=None,
        description="佔位符文字"
    )
    options: Optional[List[str]] = Field(
        default=None,
        description="選項列表（用於 select）"
    )


class ScrapeResponse(BaseModel):
    """
    v0.2 爬蟲回應模型
    符合 PRD 規格的標準化 JSON 輸出
    """
    status: str = Field(default="success", description="狀態")
    meta: MetaInfo = Field(description="元數據資訊")
    content: ContentInfo = Field(description="內容資訊")
    actions: Optional[List[ActionItem]] = Field(
        default=None,
        description="行動地圖 - 可操作元件列表"
    )
    # v0.9: 截圖支援
    screenshot_base64: Optional[str] = Field(
        default=None,
        description="頁面截圖的 Base64 編碼 (PNG)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "success",
                    "meta": {
                        "url": "https://example.com",
                        "timestamp": "2026-02-04T12:00:00Z",
                        "token_savings": "92.5%",
                        "process_time": 1.23,
                        "mode_used": "fast"
                    },
                    "content": {
                        "title": "Example Domain",
                        "markdown": "# Example Domain\n\nThis domain is for use...",
                        "raw_text_length": 500
                    },
                    "actions": [
                        {
                            "type": "button",
                            "label": "Search",
                            "selector": "#search-btn",
                            "importance": "high"
                        }
                    ]
                }
            ]
        }
    )


# ============================================================
# v0.7: 突觸交互模型 (Interact Models)
# ============================================================

class InteractRequest(BaseModel):
    """交互請求模型"""
    url: HttpUrl
    actions: List[dict] = Field(..., description="Playwright 動作列表")
    account_id: Optional[str] = Field(default=None, description="持久化 Session ID")

class InteractResponse(BaseModel):
    """交互回應模型 - v0.9"""
    status: str
    log: List[str]
    screenshot: str
    trajectory_cloud: Optional[str] = None
    points_captured: int = 0
    # v0.9: JS 執行結果
    js_results: Optional[List[dict]] = Field(
        default=None,
        description="JavaScript 執行結果列表"
    )
    # v0.9: Page state diff after interactions
    page_state: Optional[dict] = Field(
        default=None,
        description="Structured diff of page state changes (URL, cookies, DOM, console)"
    )


# ============================================================
# 錯誤模型 (Error Models)
# ============================================================

class ErrorCode(str, Enum):
    """錯誤代碼列舉"""
    INVALID_URL = "INVALID_URL"
    TARGET_TIMEOUT = "TARGET_TIMEOUT"
    TARGET_UNREACHABLE = "TARGET_UNREACHABLE"
    CAPTCHA_DETECTED = "CAPTCHA_DETECTED"
    CONTENT_TOO_LARGE = "CONTENT_TOO_LARGE"
    SELECTOR_NOT_FOUND = "SELECTOR_NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    RATE_LIMITED = "RATE_LIMITED"


class ErrorResponse(BaseModel):
    """錯誤回應模型"""
    status: str = Field(default="error", description="狀態")
    code: ErrorCode = Field(description="錯誤代碼")
    message: str = Field(description="錯誤訊息")
    details: Optional[dict] = Field(
        default=None,
        description="額外的錯誤詳情"
    )


# ============================================================
# 健康檢查模型 (Health Check Models)
# ============================================================

class HealthResponse(BaseModel):
    """健康檢查回應"""
    status: str = Field(default="healthy", description="服務狀態")
    version: str = Field(description="API 版本")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="時間戳"
    )


# ============================================================
# v0.9: 工作流模型 (Workflow Models)
# ============================================================

class WorkflowStep(BaseModel):
    """工作流步驟"""
    type: str = Field(description="步驟類型: scrape, interact, wait, assert")
    name: Optional[str] = Field(default=None, description="步驟名稱")
    url: Optional[str] = Field(default=None, description="目標 URL")
    actions: Optional[List[dict]] = Field(default=None, description="interact 動作列表")
    format: Optional[str] = Field(default="markdown")
    mode: Optional[str] = Field(default="fast")
    screenshot: bool = Field(default=False)
    timeout: Optional[int] = Field(default=None)
    extract_actions: bool = Field(default=True)
    ms: Optional[int] = Field(default=None, description="wait 步驟的等待時間 (ms)")
    condition: Optional[str] = Field(default=None, description="assert 條件")
    target: Optional[str] = Field(default=None, description="assert 目標值")
    continue_on_error: bool = Field(default=False)


class WorkflowRequest(BaseModel):
    """工作流請求"""
    steps: List[WorkflowStep] = Field(..., description="工作流步驟列表")
    context: Optional[dict] = Field(default=None, description="初始上下文 (cookies, account_id)")


class WorkflowResponse(BaseModel):
    """工作流回應"""
    status: str
    total_steps: int
    completed_steps: int
    total_time: float
    results: List[dict]


class StatsResponse(BaseModel):
    """Usage statistics response"""
    uptime_seconds: float
    total_requests: int
    scrape_count: int
    interact_count: int
    workflow_count: int
    screenshot_count: int
    js_eval_count: int
    captcha_detected: int
    errors: int
    total_tokens_saved: int
    avg_response_time: float


# ============================================================
# v0.9: Diff Models (Website Change Detection)
# ============================================================

class DiffRequest(BaseModel):
    """Website change detection request"""
    url: HttpUrl = Field(..., description="Target URL to check for changes")
    format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN,
        description="Output format for the scraped content"
    )
    mode: ScrapeMode = Field(
        default=ScrapeMode.FAST,
        description="Scrape mode: fast or visual"
    )


class DiffResponse(BaseModel):
    """Website change detection response"""
    status: str = Field(description="Status: changed / unchanged / no_previous / new_snapshot")
    url: str = Field(description="Target URL")
    message: Optional[str] = Field(default=None, description="Human-readable status message")
    added_lines: Optional[int] = Field(default=None, description="Number of added lines")
    removed_lines: Optional[int] = Field(default=None, description="Number of removed lines")
    diff: Optional[str] = Field(default=None, description="Unified diff output")
    summary: Optional[str] = Field(default=None, description="Change summary")
    previous_timestamp: Optional[float] = Field(default=None)
    current_timestamp: Optional[float] = Field(default=None)


# ============================================================
# v0.9: Queue Models (Async Task Queue)
# ============================================================

class QueueSubmitRequest(BaseModel):
    """Async task submission request"""
    url: HttpUrl = Field(..., description="Target URL to scrape asynchronously")
    format: OutputFormat = Field(default=OutputFormat.MARKDOWN)
    mode: ScrapeMode = Field(default=ScrapeMode.FAST)
    extract_actions: bool = Field(default=True)
    screenshot: bool = Field(default=False)
    timeout: Optional[int] = Field(default=60, ge=5, le=300, description="Task timeout in seconds")


class QueueSubmitResponse(BaseModel):
    """Async task submission response"""
    task_id: str = Field(description="Task ID for status polling")
    status: str = Field(default="pending", description="Initial task status")
    queue_position: int = Field(description="Current queue size")


class QueueStatusResponse(BaseModel):
    """Task status polling response"""
    id: str = Field(description="Task ID")
    status: str = Field(description="Task status: pending / running / completed / failed / timeout")
    submitted_at: float
    completed_at: Optional[float] = None
    error: Optional[str] = None
    result: Optional[dict] = Field(default=None, description="Task result (only when completed)")


# ============================================================
# v0.9: Session Management Models
# ============================================================

class SessionCreateRequest(BaseModel):
    """Create or resume a named browser session"""
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Unique session name (e.g. 'github-bot', 'amazon-checkout')"
    )
    description: str = Field(
        default="",
        description="Optional human-readable description"
    )
    ttl_hours: int = Field(
        default=24,
        ge=0,
        le=720,
        description="Time-to-live in hours (0 = no expiry)"
    )


class SessionLoginRequest(BaseModel):
    """Perform automated login with a session"""
    session_id: str = Field(..., description="Session to use for login")
    url: HttpUrl = Field(..., description="Login page URL")
    actions: List[dict] = Field(
        ...,
        description="Login actions: fill username, fill password, click submit, etc."
    )


class SessionInfo(BaseModel):
    """Session metadata"""
    session_id: str
    description: str = ""
    created_at: float
    last_used: float
    ttl_hours: int
    expires_at: Optional[float] = None
    login_url: Optional[str] = None
    login_status: str = "new"  # new | logged_in | expired
    cookies_count: int = 0
    has_state: bool = False


class SessionListResponse(BaseModel):
    """List of all managed sessions"""
    total: int
    sessions: List[SessionInfo]

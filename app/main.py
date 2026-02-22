"""
Nia-Link v0.9: AI Agent Web Neuro-Link Engine
主應用程式入口 - MCP Server 整合版
"""

import json
import time
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.routing import Mount

from .config import get_settings
from .auth import verify_api_key
from .rate_limit import check_rate_limit
from .schemas import (
    ScrapeRequest,
    ScrapeResponse,
    MetaInfo,
    ContentInfo,
    ActionItem,
    ActionType,
    Importance,
    ErrorResponse,
    ErrorCode,
    HealthResponse,
    OutputFormat,
    ScrapeMode,
    InteractRequest,
    InteractResponse,
    WorkflowRequest,
    WorkflowResponse,
    StatsResponse,
    DiffRequest,
    DiffResponse,
    QueueSubmitRequest,
    QueueSubmitResponse,
    QueueStatusResponse,
    SessionCreateRequest,
    SessionLoginRequest,
    SessionInfo,
    SessionListResponse
)
from .services.scraper import ScraperService, ScraperError
from .services.executor import ExecutorService
from .services.extractor import TokenCalculator
from .services.stats import StatsService
from .services.workflow import WorkflowService
from .services.diff import DiffService
from .services.queue import TaskQueue
from .services.session_manager import SessionManager

logger = logging.getLogger("nia-link")

# MCP Server 整合
try:
    from .mcp_server import mcp_starlette_app
    MCP_ENABLED = True
except ImportError as e:
    logger.warning(f"MCP 模組載入失敗: {e}")
    mcp_starlette_app = None
    MCP_ENABLED = False


# ============================================================
# 應用程式生命週期
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 初始化結構化日誌
    logging.basicConfig(
        level=logging.DEBUG if get_settings().debug else logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    settings = get_settings()
    logger.info(f"🚀 {settings.app_name} v{settings.app_version} 啟動中...")
    logger.info(f"📖 API 文檔: http://localhost:8000/docs")
    if MCP_ENABLED:
        logger.info(f"🔌 MCP SSE 端點: /mcp/sse")
    else:
        logger.warning(f"MCP 功能未啟用")
    yield
    logger.info(f"👋 {settings.app_name} 關閉中...")


# ============================================================
# FastAPI 應用程式
# ============================================================

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="""
## Nia-Link v0.9: AI 代理專用網頁神經連結引擎

### 🆕 v0.9 新增: Session Lifecycle & Ecosystem Ready
- **MCP SSE 端點**: `/mcp/sse` - Claude Desktop 連線入口
- **MCP Messages**: `/mcp/messages` - 訊息處理端點
- **Session 管理**: 命名會話、登入態持久化、自動過期清理

### 核心功能
- **🔍 網頁轉行動**: 將網頁轉換為結構化數據與可執行的行動地圖
- **📊 Token 經濟學**: 每次請求顯示 token_savings 節省指標
- **🗺️ Action Map**: 自動識別輸入框、按鈕、連結並生成 CSS Selector
- **⚡ 混合解析**: 預設 fast 模式，預留 visual 接口

### 認證方式
使用 Bearer Token 進行 API 認證：
```
Authorization: Bearer your-api-key
```

### MCP Tools
- `scrape_website`: 讀取網頁內容並獲取行動地圖
- `get_page_actions`: 只獲取行動地圖，節省 Token
    """,
    version="0.9.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 掛載 MCP 子應用 (帶獨立 CORS 中間件)
if MCP_ENABLED:
    app.mount("/mcp", mcp_starlette_app)

# ============================================================
# v0.7: Meta-Origin (元啟) Terminal Easter Egg
# ============================================================

@app.get("/meta-origin", tags=["v0.7 Synaptic Bridge"])
async def meta_origin():
    """
    觸發『元啟』終端介面 - v0.7 Easter Egg
    """
    terminal_art = r"""
    ============================================================
       _  _____  ___     __    ___ _   _ _  __
      | \| |_ _ / _ \ __| |  |_ _| \ | | |/ /
      | .` || || (_) / _` |   | ||  `| | ' / 
      |_|\_|___|\___/\__,_|  |___|_| \_|_|\_\ 
                                              
    >> ACCESS GRANTED: META-ORIGIN TERMINAL v0.9
    >> PROJECT ATAVISM: SYNAPTIC BRIDGE INITIALIZED
    ============================================================
    [SYSTEM STATUS]
    - NEURAL PATHS: ACTIVE
    - BEZIER MOTOR: CALIBRATED
    - TRAJECTORY CLOUD: CAPTURING...
    
    "思考即犯罪。痛覺是違禁品。"
    
    [COMMANDS AVAILABLE]
    - /v1/scrape
    - /v1/interact (New: Synaptic Tracking)
    - /mcp/sse
    ============================================================
    """
    return JSONResponse(content={"terminal": terminal_art, "status": "awakened"})

# CORS (configurable via CORS_ORIGINS env var)
cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ============================================================
# 全域例外處理
# ============================================================

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    """處理所有未預期的錯誤"""
    import traceback
    error_trace = traceback.format_exc()
    logger.error(f"Unexpected error: {error_trace}")
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": "INTERNAL_ERROR",
            "message": f"Internal scraping error: {str(exc)}",
            "details": {"error_type": type(exc).__name__}
        }
    )


@app.exception_handler(ScraperError)
async def scraper_error_handler(request, exc: ScraperError):
    """處理爬蟲錯誤"""
    error_status_map = {
        ErrorCode.INVALID_URL: status.HTTP_400_BAD_REQUEST,
        ErrorCode.TARGET_TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
        ErrorCode.TARGET_UNREACHABLE: status.HTTP_502_BAD_GATEWAY,
        ErrorCode.CONTENT_TOO_LARGE: status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        ErrorCode.SELECTOR_NOT_FOUND: status.HTTP_422_UNPROCESSABLE_ENTITY,
        ErrorCode.CAPTCHA_DETECTED: status.HTTP_403_FORBIDDEN,
    }
    
    status_code = error_status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "code": exc.code.value,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """處理 HTTP 錯誤"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {
            "status": "error",
            "code": "HTTP_ERROR",
            "message": str(exc.detail)
        }
    )


# ============================================================
# API 端點
# ============================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="健康檢查"
)
async def health_check():
    """檢查服務健康狀態"""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc)
    )


@app.get(
    "/",
    tags=["System"],
    summary="API 資訊"
)
async def root():
    """顯示 API 基本資訊"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "AI 代理專用瀏覽服務層 - v0.9 生態就緒",
        "features": ["Action Map", "Token Savings", "Hybrid Parsing", "Screenshot", "JS Sandbox", "Workflow", "CAPTCHA Detection"],
        "docs": "/docs"
    }


@app.post(
    "/v1/scrape",
    response_model=ScrapeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "無效的請求"},
        401: {"model": ErrorResponse, "description": "未授權"},
        502: {"model": ErrorResponse, "description": "目標網站無法訪問"},
        504: {"model": ErrorResponse, "description": "目標網站超時"}
    },
    tags=["Scraping"],
    summary="爬取網頁內容 (v0.2)",
    description="""
## 爬取並轉換網頁內容 - v0.2

將目標網頁的 HTML 轉換為：
- **結構化內容** (Markdown/JSON/Text)
- **行動地圖** (Action Map - 可操作元件列表)

### 核心特性
- **Token 經濟學**: 回傳 `token_savings` 百分比
- **智慧 Selector**: 自動生成 CSS Selector
- **重要性評估**: 標記 high/medium/low 重要性

### 混合引擎 (Hybrid Engine)
- **`mode=fast`** (預設): DOM 爬蟲，速度快
- **`mode=visual`**: 視覺分析，適用動態網站
    """
)
async def scrape_url(
    request: ScrapeRequest,
    api_key: str = Depends(check_rate_limit)
):
    """
    爬取指定 URL 並返回清洗後的內容與行動地圖
    """
    start_time = time.time()
    scraper = ScraperService()
    stats = StatsService()
    
    result = await scraper.scrape(
        url=str(request.url),
        output_format=request.format,
        mode=request.mode,
        wait_for_selector=request.wait_for_selector,
        timeout=request.timeout,
        extract_actions=request.extract_actions,
        cookies=request.cookies,
        screenshot=request.screenshot
    )
    
    process_time = round(time.time() - start_time, 3)
    stats.record_scrape(process_time)
    
    # 解析結果
    data = result['data']
    cost = result['cost']
    mode_used = result.get('mode_used', ScrapeMode.FAST)
    
    # 處理內容
    if request.format == OutputFormat.JSON:
        content_text = json.dumps(data['content'], ensure_ascii=False, indent=2)
    else:
        content_text = data['content']
    
    # 計算 Token 節省率
    token_savings = f"{cost.get('reduction_percent', 0)}%"
    
    # 轉換 actions 為 ActionItem 列表
    actions = None
    if data.get('actions'):
        actions = [
            ActionItem(
                type=ActionType(action['type']),
                label=action['label'],
                selector=action['selector'],
                importance=Importance(action.get('importance', 'medium')),
                value=action.get('value'),
                placeholder=action.get('placeholder'),
                options=action.get('options')
            )
            for action in data['actions']
        ]
    
    # 建構 v0.9 回應格式
    return ScrapeResponse(
        status="success",
        meta=MetaInfo(
            url=str(request.url),
            timestamp=datetime.now(timezone.utc),
            token_savings=token_savings,
            process_time=process_time,
            mode_used=mode_used
        ),
        content=ContentInfo(
            title=data.get('title') or 'Untitled',
            markdown=content_text,
            raw_text_length=cost.get('original_size', 0),
            description=data.get('metadata', {}).get('description'),
            links=data.get('links')
        ),
        actions=actions,
        screenshot_base64=result.get('screenshot_base64')  # v0.9
    )


@app.post(
    "/v1/interact",
    response_model=InteractResponse,
    tags=["v0.9 Synaptic Bridge"],
    summary="擬人化網頁交互 (v0.9)",
    description="""
## 突觸橋接交互介面 - v0.9

支援擬人化滑鼠軌跡、隨機打字抖動、JS 沙箱執行、下拉選單、捲動。

### 支援的 Action Types
- `click`: 貝茲曲線滑鼠軌跡點擊
- `fill`: 隨機延遲打字
- `evaluate`: 執行 JavaScript (帶 5s 逾時)
- `select`: 下拉選單
- `scroll`: 頁面捲動
- `upload`: 檔案上傳
- `wait`: 等待
"""
)
async def interact_url(
    request: InteractRequest,
    api_key: str = Depends(check_rate_limit)
):
    """Execute human-like interactions and return trajectory data"""
    executor = ExecutorService(headless=settings.headless)
    stats = StatsService()
    result = await executor.interact(
        url=str(request.url),
        actions=request.actions,
        account_id=request.account_id
    )
    
    if result["status"] == "error":
        stats.record_error()
        raise HTTPException(status_code=500, detail=result.get("message", "Unknown error"))
    
    stats.record_interact(0.0)
    return InteractResponse(
        status="success",
        log=result["log"],
        screenshot=result["screenshot"],
        trajectory_cloud=result.get("trajectory_cloud"),
        points_captured=result.get("points_captured", 0),
        js_results=result.get("js_results")
    )


# ============================================================
# v0.9: 工作流端點
# ============================================================

@app.post(
    "/v1/workflow",
    response_model=WorkflowResponse,
    tags=["v0.9 Workflow"],
    summary="多頁面工作流 (v0.9)",
    description="""
## 多頁面工作流 - v0.9

支援多步驟連鎖動作，每步可選：scrape / interact / wait / assert。
步驟間自動傳遞 context（cookies, actions）。

### 範例
```json
{
  "steps": [
    {"type": "scrape", "url": "https://example.com", "name": "讀取首頁"},
    {"type": "wait", "ms": 1000, "name": "等待"},
    {"type": "assert", "condition": "status_is", "target": "success"}
  ]
}
```
"""
)
async def run_workflow(
    request: WorkflowRequest,
    api_key: str = Depends(check_rate_limit)
):
    """執行多步驟工作流"""
    workflow = WorkflowService()
    steps_data = [step.model_dump() for step in request.steps]
    result = await workflow.execute(steps=steps_data, context=request.context)
    
    stats = StatsService()
    stats.record_workflow(result.get("total_time", 0))
    
    return WorkflowResponse(**result)


# ============================================================
# v0.9: Website Change Detection
# ============================================================

@app.post(
    "/v1/diff",
    response_model=DiffResponse,
    tags=["v0.9 Diff"],
    summary="Website change detection",
    description="""
## Website Change Detection - v0.9

Compare the current content of a URL against a previously saved snapshot.
Returns a unified diff and change summary.

First call saves a new snapshot. Subsequent calls compare against the previous snapshot.
"""
)
async def diff_url(
    request: DiffRequest,
    api_key: str = Depends(check_rate_limit)
):
    """Detect changes on a webpage"""
    scraper = ScraperService()
    diff_svc = DiffService()
    
    result = await scraper.scrape(
        url=str(request.url),
        output_format=request.format,
        mode=request.mode
    )
    content = result["data"].get("content", "")
    url_str = str(request.url)
    
    diff_svc.save_snapshot(url_str, content)
    diff_result = diff_svc.get_diff(url_str)
    
    if diff_result is None or diff_result.get("status") == "no_previous":
        return DiffResponse(
            status="new_snapshot",
            url=url_str,
            message="First snapshot saved. Call again to detect changes."
        )
    
    if diff_result.get("status") == "unchanged":
        return DiffResponse(
            status="unchanged",
            url=url_str,
            message="No changes detected."
        )
    
    return DiffResponse(
        status="changed",
        url=url_str,
        message="Changes detected.",
        added_lines=diff_result.get("added_lines", 0),
        removed_lines=diff_result.get("removed_lines", 0),
        diff=diff_result.get("diff"),
        summary=diff_result.get("summary"),
        previous_timestamp=diff_result.get("previous_timestamp"),
        current_timestamp=diff_result.get("current_timestamp")
    )


# ============================================================
# v0.9: Async Task Queue
# ============================================================

_task_queue = TaskQueue()


@app.post(
    "/v1/queue/submit",
    response_model=QueueSubmitResponse,
    tags=["v0.9 Queue"],
    summary="Submit async scrape task",
    description="Submit a scraping task to the background queue. Returns a task_id for polling."
)
async def queue_submit(
    request: QueueSubmitRequest,
    api_key: str = Depends(check_rate_limit)
):
    """Submit a scrape task to the async queue"""
    scraper = ScraperService()
    
    async def scrape_task():
        return await scraper.scrape(
            url=str(request.url),
            output_format=request.format,
            mode=request.mode,
            extract_actions=request.extract_actions,
            screenshot=request.screenshot
        )
    
    task_id = await _task_queue.submit(scrape_task, timeout=request.timeout)
    queue_status = _task_queue.get_queue_status()
    
    return QueueSubmitResponse(
        task_id=task_id,
        status="pending",
        queue_position=queue_status.get("queue_size", 0)
    )


@app.get(
    "/v1/queue/{task_id}",
    response_model=QueueStatusResponse,
    tags=["v0.9 Queue"],
    summary="Get task status/result",
    description="Poll for the status and result of a previously submitted async task."
)
async def queue_status(
    task_id: str,
    api_key: str = Depends(check_rate_limit)
):
    """Get async task status and result"""
    status = _task_queue.get_task_status(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return QueueStatusResponse(**status)


# ============================================================
# v0.9: Usage Statistics
# ============================================================

@app.get(
    "/v1/stats",
    response_model=StatsResponse,
    tags=["System"],
    summary="Usage statistics"
)
async def get_stats():
    """Get service usage statistics"""
    stats = StatsService()
    return StatsResponse(**stats.get_stats())


# ============================================================
# v0.9: Session Management
# ============================================================

_session_mgr = SessionManager()


@app.post(
    "/v1/session/create",
    response_model=SessionInfo,
    tags=["Session"],
    summary="Create a named browser session"
)
async def session_create(
    request: SessionCreateRequest,
    api_key: str = Depends(check_rate_limit)
):
    """Create or resume a named browser session with optional TTL."""
    meta = _session_mgr.create(
        session_id=request.session_id,
        description=request.description,
        ttl_hours=request.ttl_hours
    )
    return SessionInfo(**meta)


@app.post(
    "/v1/session/login",
    tags=["Session"],
    summary="Perform automated login with a session"
)
async def session_login(
    request: SessionLoginRequest,
    api_key: str = Depends(check_rate_limit)
):
    """Use an existing session to perform login actions. Saves cookies for future use."""
    # Ensure session exists
    meta = _session_mgr.get(request.session_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Session not found. Create it first.")
    if meta.get("login_status") == "expired":
        raise HTTPException(status_code=410, detail="Session has expired. Create a new one.")

    # Execute login actions using the Executor with session persistence
    executor = ExecutorService()
    url_str = str(request.url)
    result = await executor.interact(
        url=url_str,
        actions=request.actions,
        account_id=request.session_id
    )

    if result.get("status") == "success":
        # Count cookies from saved state
        state_path = _session_mgr.get_storage_state_path(request.session_id)
        cookies_count = 0
        if state_path:
            try:
                import json as _json
                with open(state_path, "r") as f:
                    state = _json.load(f)
                cookies_count = len(state.get("cookies", []))
            except Exception:
                pass
        
        _session_mgr.update_login_status(
            session_id=request.session_id,
            login_url=url_str,
            status="logged_in",
            cookies_count=cookies_count
        )
        stats = StatsService()
        stats.record_interact(time.time())

    return {
        "status": result.get("status"),
        "session_id": request.session_id,
        "login_status": "logged_in" if result.get("status") == "success" else "failed",
        "log": result.get("log", []),
        "cookies_count": cookies_count if result.get("status") == "success" else 0,
        "screenshot_base64": result.get("screenshot_base64")
    }


@app.get(
    "/v1/session/list",
    response_model=SessionListResponse,
    tags=["Session"],
    summary="List all managed sessions"
)
async def session_list(
    api_key: str = Depends(check_rate_limit)
):
    """List all browser sessions with their metadata and login status."""
    sessions = _session_mgr.list_sessions()
    return SessionListResponse(
        total=len(sessions),
        sessions=[SessionInfo(**s) for s in sessions]
    )


@app.delete(
    "/v1/session/{session_id}",
    tags=["Session"],
    summary="Delete a session"
)
async def session_delete(
    session_id: str,
    api_key: str = Depends(check_rate_limit)
):
    """Delete a session and all its stored cookies/state."""
    deleted = _session_mgr.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}


# ============================================================
# 開發模式入口
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

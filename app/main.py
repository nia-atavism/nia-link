"""
Nia-Link v0.9: AI Agent Web Neuro-Link Engine
主應用程式入口 - MCP Server 整合版
"""

import json
import time
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.routing import Mount
import os

# 👇 引入防護盾模組 (Rate Limiting)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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
    from .mcp_server import mcp_starlette_app, session_manager
    MCP_ENABLED = True
except ImportError as e:
    logger.warning(f"MCP 模組載入失敗: {e}")
    mcp_starlette_app = None
    session_manager = None
    MCP_ENABLED = False


# ============================================================
# 應用程式生命週期
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期 management"""
    # 初始化結構化日誌
    logging.basicConfig(
        level=logging.DEBUG if get_settings().debug else logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    settings = get_settings()
    logger.info(f"🚀 {settings.app_name} v{settings.app_version} 啟動中...")
    logger.info(f"📖 API 文檔: http://localhost:8000/docs")
    
    try:
        if MCP_ENABLED and session_manager:
            logger.info(f"🔌 MCP Streamable HTTP 端點: /mcp/")
            logger.info(f"🔌 MCP SSE 端點: /mcp/sse")
            # 關鍵：在主應用生命週期中啟動 MCP 的非同步任務群組
            async with session_manager.run():
                yield
        else:
            logger.warning(f"MCP 功能未啟用")
            yield
    finally:
        logger.info(f"👋 {settings.app_name} 關閉中...")


# ============================================================
# FastAPI 應用程式
# ============================================================

settings = get_settings()

# 建立防護盾實體，使用訪客的真實 IP 作為追蹤基準
limiter = Limiter(key_func=get_remote_address)

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

# 將防護盾註冊進 FastAPI 的全域狀態與異常處理器中
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 掛載 MCP 子應用 (帶獨立 CORS 中間件)
if MCP_ENABLED:
    app.mount("/mcp", mcp_starlette_app)

# ============================================================
# API 端點 (必須在靜態掛載前，否則會被 catch-all 攔截)
# ============================================================

@app.get("/health", response_model=HealthResponse, tags=["System"], summary="健康檢查")
async def health_check():
    """檢查服務健康狀態"""
    return HealthResponse(status="healthy", version=settings.app_version, timestamp=datetime.now(timezone.utc))

@app.get("/v1/info", tags=["System"], summary="API 資訊")
async def api_info():
    """顯示 API 基本資訊"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "AI 代理專用瀏覽服務層 - v0.9 生態就緒",
        "features": ["Action Map", "Token Savings", "Hybrid Parsing", "Screenshot", "JS Sandbox", "Workflow", "CAPTCHA Detection"],
        "docs": "/docs"
    }

@app.post("/v1/scrape", response_model=ScrapeResponse, tags=["Scraping"], summary="爬取網頁內容 (v0.2)")
@limiter.limit("5/minute")
async def scrape_url(request: Request, scrape_data: ScrapeRequest):
    start_time = time.time()
    scraper = ScraperService()
    stats = StatsService()
    result = await scraper.scrape(url=str(scrape_data.url), output_format=scrape_data.format, mode=scrape_data.mode, wait_for_selector=scrape_data.wait_for_selector, timeout=scrape_data.timeout, extract_actions=scrape_data.extract_actions, cookies=scrape_data.cookies, screenshot=scrape_data.screenshot)
    process_time = round(time.time() - start_time, 3)
    stats.record_scrape(process_time)
    data = result['data']; cost = result['cost']
    content_text = json.dumps(data['content'], ensure_ascii=False, indent=2) if scrape_data.format == OutputFormat.JSON else data['content']
    actions = [ActionItem(type=ActionType(a['type']), label=a['label'], selector=a['selector'], importance=Importance(a.get('importance', 'medium')), value=a.get('value'), placeholder=a.get('placeholder'), options=a.get('options')) for a in data['actions']] if data.get('actions') else None
    return ScrapeResponse(status="success", meta=MetaInfo(url=str(scrape_data.url), timestamp=datetime.now(timezone.utc), token_savings=f"{cost.get('reduction_percent', 0)}%", process_time=process_time, mode_used=result.get('mode_used', ScrapeMode.FAST)), content=ContentInfo(title=data.get('title') or 'Untitled', markdown=content_text, raw_text_length=cost.get('original_size', 0), description=data.get('metadata', {}).get('description'), links=data.get('links')), actions=actions, screenshot_base64=result.get('screenshot_base64'))

@app.post("/v1/interact", response_model=InteractResponse, tags=["v0.9 Synaptic Bridge"], summary="擬人化網頁交互 (v0.9)")
async def interact_url(request: InteractRequest, api_key: str = Depends(check_rate_limit)):
    executor = ExecutorService(headless=settings.headless)
    stats = StatsService()
    result = await executor.interact(url=str(request.url), actions=request.actions, account_id=request.account_id)
    if result["status"] == "error":
        stats.record_error()
        raise HTTPException(status_code=500, detail=result.get("message", "Unknown error"))
    stats.record_interact(0.0)
    return InteractResponse(status="success", log=result["log"], screenshot=result["screenshot"], trajectory_cloud=result.get("trajectory_cloud"), points_captured=result.get("points_captured", 0), js_results=result.get("js_results"))

@app.post("/v1/workflow", response_model=WorkflowResponse, tags=["v0.9 Workflow"], summary="多頁面工作流 (v0.9)")
async def run_workflow(request: WorkflowRequest, api_key: str = Depends(check_rate_limit)):
    workflow = WorkflowService()
    result = await workflow.execute(steps=[step.model_dump() for step in request.steps], context=request.context)
    StatsService().record_workflow(result.get("total_time", 0))
    return WorkflowResponse(**result)

@app.post("/v1/diff", response_model=DiffResponse, tags=["v0.9 Diff"], summary="Website change detection")
async def diff_url(request: DiffRequest, api_key: str = Depends(check_rate_limit)):
    scraper = ScraperService(); diff_svc = DiffService()
    result = await scraper.scrape(url=str(request.url), output_format=request.format, mode=request.mode)
    content = result["data"].get("content", ""); url_str = str(request.url)
    diff_svc.save_snapshot(url_str, content)
    diff_result = diff_svc.get_diff(url_str)
    if diff_result is None or diff_result.get("status") == "no_previous":
        return DiffResponse(status="new_snapshot", url=url_str, message="First snapshot saved. Call again to detect changes.")
    if diff_result.get("status") == "unchanged":
        return DiffResponse(status="unchanged", url=url_str, message="No changes detected.")
    return DiffResponse(status="changed", url=url_str, message="Changes detected.", added_lines=diff_result.get("added_lines", 0), removed_lines=diff_result.get("removed_lines", 0), diff=diff_result.get("diff"), summary=diff_result.get("summary"), previous_timestamp=diff_result.get("previous_timestamp"), current_timestamp=diff_result.get("current_timestamp"))

_task_queue = TaskQueue()
@app.post("/v1/queue/submit", response_model=QueueSubmitResponse, tags=["v0.9 Queue"], summary="Submit async scrape task")
async def queue_submit(request: QueueSubmitRequest, api_key: str = Depends(check_rate_limit)):
    scraper = ScraperService()
    task_id = await _task_queue.submit(lambda: scraper.scrape(url=str(request.url), output_format=request.format, mode=request.mode, extract_actions=request.extract_actions, screenshot=request.screenshot), timeout=request.timeout)
    return QueueSubmitResponse(task_id=task_id, status="pending", queue_position=_task_queue.get_queue_status().get("queue_size", 0))

@app.get("/v1/queue/{task_id}", response_model=QueueStatusResponse, tags=["v0.9 Queue"], summary="Get task status/result")
async def queue_status(task_id: str, api_key: str = Depends(check_rate_limit)):
    status = _task_queue.get_task_status(task_id)
    if status is None: raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return QueueStatusResponse(**status)

@app.get("/v1/stats", response_model=StatsResponse, tags=["System"], summary="Usage statistics")
async def get_stats():
    return StatsResponse(**StatsService().get_stats())

_session_mgr = SessionManager()
@app.post("/v1/session/create", response_model=SessionInfo, tags=["Session"], summary="Create a named browser session")
async def session_create(request: SessionCreateRequest, api_key: str = Depends(check_rate_limit)):
    return SessionInfo(**_session_mgr.create(session_id=request.session_id, description=request.description, ttl_hours=request.ttl_hours))

@app.post("/v1/session/login", tags=["Session"], summary="Perform automated login with a session")
async def session_login(request: SessionLoginRequest, api_key: str = Depends(check_rate_limit)):
    meta = _session_mgr.get(request.session_id)
    if not meta: raise HTTPException(status_code=404, detail="Session not found.")
    result = await ExecutorService().interact(url=str(request.url), actions=request.actions, account_id=request.session_id)
    cookies_count = 0
    if result.get("status") == "success":
        state_path = _session_mgr.get_storage_state_path(request.session_id)
        if state_path:
            try:
                with open(state_path, "r") as f: cookies_count = len(json.load(f).get("cookies", []))
            except: pass
        _session_mgr.update_login_status(session_id=request.session_id, login_url=str(request.url), status="logged_in", cookies_count=cookies_count)
        StatsService().record_interact(time.time())
    return {"status": result.get("status"), "session_id": request.session_id, "login_status": "logged_in" if result.get("status") == "success" else "failed", "log": result.get("log", []), "cookies_count": cookies_count, "screenshot_base64": result.get("screenshot_base64")}

@app.get("/v1/session/list", response_model=SessionListResponse, tags=["Session"], summary="List all managed sessions")
async def session_list(api_key: str = Depends(check_rate_limit)):
    sessions = _session_mgr.list_sessions()
    return SessionListResponse(total=len(sessions), sessions=[SessionInfo(**s) for s in sessions])

@app.delete("/v1/session/{session_id}", tags=["Session"], summary="Delete a session")
async def session_delete(session_id: str, api_key: str = Depends(check_rate_limit)):
    if not _session_mgr.delete(session_id): raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}

@app.get("/meta-origin", tags=["v0.7 Synaptic Bridge"])
async def meta_origin():
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

# --- v0.9: 前端靜態檔案掛載 ---
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
    
    # 這裡加入一個萬用路徑處理，避免前端路由重新整理後 404，或者首頁邏輯被覆蓋
    @app.get("/{full_path:path}", include_in_schema=False)
    async def catch_all(full_path: str):
        if full_path.startswith("v1/") or full_path.startswith("mcp/") or full_path.startswith("health") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

# CORS
cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["*"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

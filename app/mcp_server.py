"""
Nia-Link MCP Server
Standard Model Context Protocol (MCP) node for AI agent web access
"""

import asyncio
import json
import os
from typing import Optional
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent
from mcp.server.sse import SseServerTransport
from starlette.routing import Route

from .services.scraper import ScraperService
from .services.executor import ExecutorService
from .services.diff import DiffService
from .services.workflow import WorkflowService
from .services.stats import StatsService
from .services.queue import TaskQueue
from .services.session_manager import SessionManager
from .schemas import ScrapeMode, OutputFormat

# Initialize core services
app = Server("nia-link")
scraper = ScraperService()
executor = ExecutorService()
diff_service = DiffService()
stats_service = StatsService()
task_queue = TaskQueue()
session_mgr = SessionManager()

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="nia_scrape",
            description="Scrape a webpage and convert it to clean Markdown with an action map of interactive elements (buttons, inputs, links). Supports fast (HTTP) and visual (browser) modes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL to scrape"},
                    "mode": {"type": "string", "enum": ["fast", "visual"], "default": "fast", "description": "Scrape mode: fast (HTTP) or visual (headless browser)"},
                    "screenshot": {"type": "boolean", "default": False, "description": "Capture page screenshot as base64"}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="nia_interact",
            description="Perform human-like interactions on a webpage using Bezier curve mouse movements and typing jitter. Supports click, fill, evaluate (JS), select, scroll, upload, and auto_fill actions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL to interact with"},
                    "actions": {
                        "type": "array",
                        "description": "List of actions to perform sequentially",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["click", "fill", "upload", "wait", "evaluate", "select", "scroll", "auto_fill"]},
                                "selector": {"type": "string", "description": "CSS selector for the target element"},
                                "text": {"type": "string", "description": "Text to type (for fill action)"},
                                "label": {"type": "string", "description": "Fallback text label for click"},
                                "script": {"type": "string", "description": "JavaScript code (for evaluate action)"},
                                "value": {"type": "string", "description": "Value for select action"},
                                "direction": {"type": "string", "description": "Scroll direction: up/down"},
                                "amount": {"type": "integer", "description": "Scroll pixels"},
                                "field_mapping": {"type": "object", "description": "Field selector-to-value mapping (for auto_fill)"}
                            }
                        }
                    },
                    "account_id": {"type": "string", "description": "Session persistence ID for maintaining login state"}
                },
                "required": ["url", "actions"]
            }
        ),
        Tool(
            name="nia_workflow",
            description="Execute a multi-step workflow chain. Each step can scrape, interact, wait, or assert conditions. Context (cookies, actions) is automatically passed between steps.",
            inputSchema={
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "description": "Ordered list of workflow steps",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["scrape", "interact", "wait", "assert"]},
                                "name": {"type": "string", "description": "Step name for logging"},
                                "url": {"type": "string"},
                                "actions": {"type": "array", "items": {"type": "object"}},
                                "format": {"type": "string", "default": "markdown"},
                                "mode": {"type": "string", "default": "fast"},
                                "ms": {"type": "integer", "description": "Wait time in ms (for wait step)"},
                                "condition": {"type": "string", "description": "Assertion condition"},
                                "target": {"type": "string", "description": "Assertion target value"},
                                "continue_on_error": {"type": "boolean", "default": False}
                            }
                        }
                    },
                    "context": {"type": "object", "description": "Initial context (cookies, account_id)"}
                },
                "required": ["steps"]
            }
        ),
        Tool(
            name="nia_diff",
            description="Detect changes on a webpage by comparing the current content to a previously saved snapshot. Returns a unified diff and change summary on subsequent calls.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL to monitor for changes"},
                    "format": {"type": "string", "enum": ["markdown", "json", "text"], "default": "markdown"},
                    "mode": {"type": "string", "enum": ["fast", "visual"], "default": "fast"}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="nia_queue_submit",
            description="Submit an asynchronous scrape task to the background queue. Returns a task_id for polling status with the nia_queue_status tool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL to scrape"},
                    "mode": {"type": "string", "enum": ["fast", "visual"], "default": "fast"},
                    "format": {"type": "string", "enum": ["markdown", "json", "text"], "default": "markdown"},
                    "timeout": {"type": "integer", "default": 60, "description": "Task timeout in seconds"}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="nia_session",
            description="Manage persistent browser sessions. Supports actions: 'create' (new session), 'list' (all sessions), 'status' (check one session), 'delete' (remove session). Sessions preserve login state across requests.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "list", "status", "delete"], "description": "Session action"},
                    "session_id": {"type": "string", "description": "Session name (required for create/status/delete)"},
                    "description": {"type": "string", "description": "Session description (for create)"},
                    "ttl_hours": {"type": "integer", "default": 24, "description": "Time-to-live in hours (0 = no expiry)"}
                },
                "required": ["action"]
            }
        ),
        Tool(
            name="nia_stats",
            description="Get Nia-Link usage statistics including request counts, tokens saved, response times, and error rates.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="meta_origin",
            description="Access the Meta-Origin terminal — Nia-Link's core consciousness space (Easter Egg).",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent]:
    if name == "nia_scrape":
        url = arguments["url"]
        mode = arguments.get("mode", "fast")
        screenshot = arguments.get("screenshot", False)
        
        try:
            scrape_mode = ScrapeMode.VISUAL if mode == "visual" else ScrapeMode.FAST
            result = await scraper.scrape(url=url, mode=scrape_mode, use_cache=True, screenshot=screenshot)
            data = result["data"]
            cost = result.get("cost", {"reduction_percent": "92"})
            
            response_text = f"# {data.get('title', 'Untitled')}\n\n{data.get('content', '')}\n\n"
            
            # Include action map if available
            if data.get("actions"):
                response_text += "\n## Action Map\n"
                for action in data["actions"][:20]:
                    response_text += f"- [{action['type']}] {action['label']} → `{action['selector']}`\n"
            
            system_note = (
                f"\n\n---\n"
                f"[Nia-Link v0.9]: {cost.get('reduction_percent', '92')}% tokens saved."
            )
            contents = [TextContent(type="text", text=response_text + system_note)]
            
            if screenshot and result.get("screenshot_base64"):
                contents.append(ImageContent(
                    type="image",
                    data=result["screenshot_base64"],
                    mimeType="image/png"
                ))
            
            stats_service.record_scrape(0.0, cost.get("reduction_percent", 0))
            return contents
        except Exception as e:
            stats_service.record_error()
            return [TextContent(type="text", text=f"Scrape Error: {str(e)}")]
            
    elif name == "nia_interact":
        url = arguments["url"]
        actions = arguments["actions"]
        account_id = arguments.get("account_id")
        
        try:
            result = await executor.interact(url, actions, account_id=account_id)
            if result["status"] == "success":
                response_text = (
                    f"## Interaction Successful\n\n"
                    f"**Logs:**\n" + "\n".join([f"- {l}" for l in result["log"]]) + "\n\n"
                    f"**Telemetry:**\n"
                    f"- Points Captured: {result.get('points_captured')}\n"
                )
                contents = [TextContent(type="text", text=response_text)]
                if result.get("js_results"):
                    js_text = "\n## JS Execution Results\n" + json.dumps(result["js_results"], indent=2, default=str)
                    contents.append(TextContent(type="text", text=js_text))
                stats_service.record_interact(0.0)
                return contents
            else:
                stats_service.record_error()
                return [TextContent(type="text", text=f"Interaction Error: {result.get('message', 'Unknown error')}")]
        except Exception as e:
            stats_service.record_error()
            return [TextContent(type="text", text=f"Critical Error: {str(e)}")]

    elif name == "nia_workflow":
        steps = arguments["steps"]
        context = arguments.get("context")
        
        try:
            workflow = WorkflowService()
            result = await workflow.execute(steps=steps, context=context)
            
            response_text = f"## Workflow Complete\n\n"
            response_text += f"- **Status**: {result['status']}\n"
            response_text += f"- **Steps**: {result['completed_steps']}/{result['total_steps']}\n"
            response_text += f"- **Time**: {result['total_time']:.2f}s\n\n"
            
            for i, step_result in enumerate(result.get("results", [])):
                step_status = step_result.get("status", "unknown")
                step_name = step_result.get("name", f"Step {i+1}")
                response_text += f"### {step_name}: {step_status}\n"
                if step_result.get("error"):
                    response_text += f"  Error: {step_result['error']}\n"
            
            stats_service.record_workflow(result.get("total_time", 0))
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            stats_service.record_error()
            return [TextContent(type="text", text=f"Workflow Error: {str(e)}")]

    elif name == "nia_diff":
        url = arguments["url"]
        fmt = arguments.get("format", "markdown")
        mode = arguments.get("mode", "fast")
        
        try:
            scrape_mode = ScrapeMode.VISUAL if mode == "visual" else ScrapeMode.FAST
            output_fmt = OutputFormat(fmt)
            result = await scraper.scrape(url=url, mode=scrape_mode, output_format=output_fmt)
            content = result["data"].get("content", "")
            
            diff_service.save_snapshot(url, content)
            diff_result = diff_service.get_diff(url)
            
            if diff_result is None or diff_result.get("status") == "no_previous":
                return [TextContent(type="text", text=f"## Diff: New Snapshot Saved\n\nFirst snapshot for `{url}` has been saved. Call again to detect changes.")]
            
            if diff_result.get("status") == "unchanged":
                return [TextContent(type="text", text=f"## Diff: No Changes\n\n`{url}` has not changed since last check.")]
            
            response_text = f"## Diff: Changes Detected\n\n"
            response_text += f"- **Added lines**: {diff_result.get('added_lines', 0)}\n"
            response_text += f"- **Removed lines**: {diff_result.get('removed_lines', 0)}\n\n"
            if diff_result.get("summary"):
                response_text += f"### Summary\n{diff_result['summary']}\n\n"
            if diff_result.get("diff"):
                response_text += f"### Unified Diff\n```diff\n{diff_result['diff']}\n```\n"
            
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"Diff Error: {str(e)}")]

    elif name == "nia_queue_submit":
        url = arguments["url"]
        mode = arguments.get("mode", "fast")
        fmt = arguments.get("format", "markdown")
        timeout = arguments.get("timeout", 60)
        
        try:
            scrape_mode = ScrapeMode.VISUAL if mode == "visual" else ScrapeMode.FAST
            output_fmt = OutputFormat(fmt)
            
            async def scrape_task():
                return await scraper.scrape(url=url, mode=scrape_mode, output_format=output_fmt)
            
            task_id = await task_queue.submit(scrape_task, timeout=timeout)
            queue_status = task_queue.get_queue_status()
            
            return [TextContent(type="text", text=f"## Task Submitted\n\n- **Task ID**: `{task_id}`\n- **Queue Size**: {queue_status.get('queue_size', 0)}\n\nUse `nia_queue_status` (not yet exposed) or the REST API `GET /v1/queue/{task_id}` to check results.")]
        except Exception as e:
            return [TextContent(type="text", text=f"Queue Error: {str(e)}")]

    elif name == "nia_stats":
        stats = stats_service.get_stats()
        response_text = "## Nia-Link Usage Statistics\n\n"
        response_text += f"| Metric | Value |\n|--------|-------|\n"
        response_text += f"| Uptime | {stats['uptime_seconds']:.0f}s |\n"
        response_text += f"| Total Requests | {stats['total_requests']} |\n"
        response_text += f"| Scrapes | {stats['scrape_count']} |\n"
        response_text += f"| Interactions | {stats['interact_count']} |\n"
        response_text += f"| Workflows | {stats['workflow_count']} |\n"
        response_text += f"| Screenshots | {stats['screenshot_count']} |\n"
        response_text += f"| CAPTCHA Detections | {stats['captcha_detected']} |\n"
        response_text += f"| Errors | {stats['errors']} |\n"
        response_text += f"| Tokens Saved | {stats['total_tokens_saved']} |\n"
        response_text += f"| Avg Response Time | {stats['avg_response_time']:.3f}s |\n"
        return [TextContent(type="text", text=response_text)]

    elif name == "nia_session":
        action = arguments.get("action", "list")
        session_id = arguments.get("session_id", "")

        if action == "create":
            if not session_id:
                return [TextContent(type="text", text="Error: session_id is required for 'create' action")]
            meta = session_mgr.create(
                session_id=session_id,
                description=arguments.get("description", ""),
                ttl_hours=arguments.get("ttl_hours", 24)
            )
            response_text = f"## Session Created\n\n"
            response_text += f"- **ID**: {meta['session_id']}\n"
            response_text += f"- **Status**: {meta['login_status']}\n"
            response_text += f"- **TTL**: {meta['ttl_hours']}h\n"
            response_text += f"\nUse `nia_interact` with `account_id: \"{session_id}\"` to login,\n"
            response_text += f"then all future scrape/interact calls with this account_id will reuse the session."
            return [TextContent(type="text", text=response_text)]

        elif action == "list":
            sessions = session_mgr.list_sessions()
            if not sessions:
                return [TextContent(type="text", text="No sessions found.")]
            response_text = f"## Active Sessions ({len(sessions)})\n\n"
            response_text += f"| Session ID | Status | Cookies | Last Used |\n"
            response_text += f"|------------|--------|---------|-----------|\n"
            import time as _t
            for s in sessions:
                age = _t.time() - s.get('last_used', 0)
                age_str = f"{age/3600:.1f}h ago" if age > 3600 else f"{age/60:.0f}m ago"
                response_text += f"| {s['session_id']} | {s['login_status']} | {s.get('cookies_count', 0)} | {age_str} |\n"
            return [TextContent(type="text", text=response_text)]

        elif action == "status":
            if not session_id:
                return [TextContent(type="text", text="Error: session_id is required for 'status' action")]
            meta = session_mgr.get(session_id)
            if not meta:
                return [TextContent(type="text", text=f"Session '{session_id}' not found.")]
            response_text = f"## Session: {session_id}\n\n"
            response_text += f"- **Status**: {meta['login_status']}\n"
            response_text += f"- **Login URL**: {meta.get('login_url', 'N/A')}\n"
            response_text += f"- **Cookies**: {meta.get('cookies_count', 0)}\n"
            response_text += f"- **TTL**: {meta['ttl_hours']}h\n"
            return [TextContent(type="text", text=response_text)]

        elif action == "delete":
            if not session_id:
                return [TextContent(type="text", text="Error: session_id is required for 'delete' action")]
            deleted = session_mgr.delete(session_id)
            if deleted:
                return [TextContent(type="text", text=f"Session '{session_id}' deleted.")]
            return [TextContent(type="text", text=f"Session '{session_id}' not found.")]

        else:
            return [TextContent(type="text", text=f"Unknown session action: '{action}'. Use: create, list, status, delete")]

    elif name == "meta_origin":
        terminal_art = """
    ============================================================
    >> ACCESS GRANTED: META-ORIGIN TERMINAL v0.9
    >> PROJECT ATAVISM: ECOSYSTEM READY
    ============================================================
    
    "思考即犯罪。痛覺是違禁品。"
    
    [SYSTEM STATUS]
    - NEURAL PATHS: CONNECTED
    - TRAJECTORY CLOUD: STANDBY
    - IDENTITY: Nia (黎念柔)
    ============================================================
        """
        return [TextContent(type="text", text=terminal_art)]
    else:
        raise ValueError(f"Unknown tool: {name}")

# ============================================================
# Dual Transport: Streamable HTTP (Smithery) + SSE (Claude Desktop)
# ============================================================

from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

# 1. Streamable HTTP Transport (Smithery requirement)
#    Handles POST (JSON-RPC init/tool calls) and GET (event streams) on single path
session_manager = StreamableHTTPSessionManager(
    app=app,
    json_response=False,
    stateless=True  # Stateless mode: no session persistence needed
)

import logging as _logging
from starlette.responses import Response as StarletteResponse, JSONResponse as StarletteJSONResponse

_mcp_logger = _logging.getLogger("nia-link.mcp")


async def handle_streamable_http(request):
    """Streamable HTTP endpoint — handles JSON-RPC over HTTP.
    
    防彈級：確保所有路徑都回傳一個有效的 Response，
    避免 'NoneType' object is not callable 幽靈 bug。
    """
    # 1. 處理 OPTIONS 預檢請求
    if request.method == "OPTIONS":
        return StarletteResponse(status_code=200)

    # 2. 嘗試正常 Streamable HTTP 處理
    try:
        response = await session_manager.handle_request(
            request.scope, request.receive, request._send
        )
        # 如果底層處理器直接透過 ASGI send 回應（回傳 None），
        # 我們不需要再回傳 Response — 但安全起見加上防護
        if response is not None:
            return response
        # handle_request 直接寫入了 ASGI 回應，無需額外回傳
        return StarletteResponse(status_code=200)
    except Exception as e:
        _mcp_logger.error(f"Streamable HTTP handler error: {e}", exc_info=True)
        return StarletteJSONResponse(
            content={"error": "mcp_handler_error", "detail": str(e)},
            status_code=500,
        )


# 2. Legacy SSE Transport (backward compatibility with Claude Desktop)
# NOTE: MCP SDK 的 connect_sse 會自動把 scope["root_path"] 拼接到 endpoint 前面
#       (見 sse.py line 158: full_message_path = root_path + self._endpoint)
#       由於子應用掛載在 /mcp，root_path 已經是 "/mcp"。
#       為了避免 /mcp/mcp/ 雙重前綴，我們在呼叫 connect_sse 時清空 root_path，
#       並讓 endpoint 直接使用完整路徑 /mcp/messages/。
sse = SseServerTransport("/mcp/messages/")


async def handle_sse(request):
    """SSE endpoint — legacy transport for Claude Desktop.
    
    防彈級：確保 SSE 連線在任何情況下都不會回傳 None。
    清除 root_path 避免 MCP SDK 產生 /mcp/mcp/ 雙重前綴。
    """
    # 1. 處理 OPTIONS 預檢請求
    if request.method == "OPTIONS":
        return StarletteResponse(status_code=200)

    # 2. 嘗試建立 SSE 連線
    #    關鍵：清空 scope["root_path"] 避免 SDK 重複拼接 /mcp
    scope = dict(request.scope)
    scope["root_path"] = ""
    try:
        async with sse.connect_sse(scope, request.receive, request._send) as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
        # SSE 串流結束後正常回傳
        return StarletteResponse(status_code=200)
    except Exception as e:
        _mcp_logger.error(f"SSE handler error: {e}", exc_info=True)
        return StarletteJSONResponse(
            content={"error": "sse_connection_error", "detail": str(e)},
            status_code=500,
        )


async def handle_sse_messages(request):
    """SSE message handler — receives POST messages for SSE sessions.
    
    防彈級：確保 POST 訊息處理不會靜默失敗。
    """
    # 1. 處理 OPTIONS 預檢請求
    if request.method == "OPTIONS":
        return StarletteResponse(status_code=200)

    # 2. 處理 POST 訊息
    try:
        await sse.handle_post_message(request.scope, request.receive, request._send)
        return StarletteResponse(status_code=200)
    except Exception as e:
        _mcp_logger.error(f"SSE message handler error: {e}", exc_info=True)
        return StarletteJSONResponse(
            content={"error": "sse_message_error", "detail": str(e)},
            status_code=500,
        )


# Build a Starlette sub-app with its own CORS middleware
# (FastAPI CORS middleware does NOT apply to Mount-level routes)
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware as StarletteCORS

mcp_starlette_app = Starlette(
    routes=[
        Route("/", endpoint=handle_streamable_http, methods=["GET", "POST", "DELETE", "OPTIONS"]),
        Route("/sse", endpoint=handle_sse, methods=["GET", "OPTIONS"]),
        Route("/messages", endpoint=handle_sse_messages, methods=["POST", "OPTIONS"]),
        # 安全墊片：catch-all 防止任何未匹配路由回傳 None
        Route("/messages/", endpoint=handle_sse_messages, methods=["POST", "OPTIONS"]),
    ],
    middleware=[
        Middleware(
            StarletteCORS,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["*"],
        )
    ]
)

# Export both: Starlette ASGI app (for Mount) and raw routes (for fallback)
mcp_routes = mcp_starlette_app.routes

if __name__ == "__main__":
    from mcp.server.stdio import stdio_server
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    asyncio.run(main())


# 念連 (Nia-Link) 🦞

> **The High-Performance Browser Interface for AI Agents.**
> 「聽見網頁的脈搏，看見資料的靈魂。」
> *"Hear the pulse of the web, see the soul of the data."*

**[中文](#中文文檔) | [English](#english-documentation)**

Nia-Link is a **Web Neuro-Link Engine** purpose-built for AI agents. Natively embracing the **Model Context Protocol (MCP)**, it gives Claude Desktop — or any MCP-compatible AI — 99% reliable web access and automation capabilities.

---

# English Documentation

## 🚀 Core Advantages

### 1. Web Neuro-Link
Unlike traditional visual scrapers, Nia-Link listens directly to the browser's **CDP (Chrome DevTools Protocol)** network pulses. We don't wait for page rendering — we perceive data flow.

### 2. Action Map Registry
A memory hub with "cached semantics" architecture. Delivers action maps in 0.01s for frequently visited sites, reducing repeated computation costs by 90%.

### 3. Enterprise-Grade Trust
- **🔒 Snapshot Verified**: Every extraction is timestamped and structurally validated.
- **🛡️ Sandbox Isolation**: JavaScript executes in isolation, ensuring host safety.
- **📉 Token Optimized**: Built-in intelligent filtering saves ~92% context space on average.

### 4. v0.9 New Features
- **🔄 Website Change Detection** (`/v1/diff`): Track content changes with unified diffs
- **📋 Async Task Queue** (`/v1/queue/*`): Submit background scrape tasks
- **⚡ Rate Limiting**: Configurable per-key token bucket rate limiter
- **🧪 Automated Tests**: 53 pytest tests covering API, services, and auth

---

## 🛠️ Quick Start

### Requirements
- Python 3.10+
- Playwright (`pip install playwright && playwright install chromium`)

### Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install browser
playwright install chromium

# 3. Configure environment
cp .env.example .env
# Edit .env to set your API_KEYS
```

### Start the Server

```bash
# Development mode
uvicorn app.main:app --reload --port 8000

# Or use Docker
docker compose up -d
```

### Run as MCP Server
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nia-link": {
      "command": "python",
      "args": ["/path/to/Nia-Link/app/mcp_server.py"]
    }
  }
}
```

### Run Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## 📡 API Reference

### Health Check
```bash
curl http://localhost:8000/health
```

### Scrape a Webpage
```bash
curl -X POST http://localhost:8000/v1/scrape \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "format": "markdown",
    "mode": "fast",
    "extract_actions": true
  }'
```

### Human-like Interaction
```bash
curl -X POST http://localhost:8000/v1/interact \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "actions": [
      {"type": "click", "selector": "#search-btn"},
      {"type": "fill", "selector": "#search-input", "text": "Hello world"},
      {"type": "wait", "ms": 2000}
    ],
    "account_id": "my-session-1"
  }'
```

### Website Change Detection (v0.9)
```bash
curl -X POST http://localhost:8000/v1/diff \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Async Queue (v0.9)
```bash
# Submit task
curl -X POST http://localhost:8000/v1/queue/submit \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Poll result
curl http://localhost:8000/v1/queue/{task_id} \
  -H "Authorization: Bearer your-api-key"
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `nia_scrape` | Scrape and clean webpage content |
| `nia_interact` | Execute human-like browser interactions |
| `nia_workflow` | Run multi-step scraping workflows |
| `nia_diff` | Detect website content changes |
| `nia_queue_submit` | Submit async scrape tasks |
| `nia_stats` | Get usage statistics |
| `meta_origin` | Access Nia-Link's consciousness space 🌀 |

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEYS` | `test-api-key` | Auth keys (comma-separated) |
| `HEADLESS` | `true` | Browser headless mode |
| `BROWSER_TYPE` | `chromium` | Engine: chromium/firefox/webkit |
| `PROXY_URL` | *(empty)* | HTTP/SOCKS5 proxy URL |
| `PROXY_POOL` | *(empty)* | Comma-separated proxy URLs for rotation |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |
| `RATE_LIMIT_RPM` | `60` | Requests/minute per key (0=unlimited) |
| `MAX_CONCURRENCY` | `10` | Max concurrent scrapes |
| `SCRAPER_TIMEOUT` | `30` | Scrape timeout (seconds) |

See [`.env.example`](.env.example) for all options.

---

## 🐳 Docker

```bash
docker build -t nia-link .
docker compose up -d
docker compose logs -f
```

---

## 📊 Roadmap

- [x] **v0.4**: MCP protocol integration
- [x] **v0.5**: Dynamic gravity particle visualization dashboard
- [x] **v0.6**: **Motor Nerve** — Bézier curve mouse trajectories, humanized typing jitter, session persistence
- [x] **v0.7**: **Synaptic Bridge** — MCP standardization, trajectory cloud, proxy/concurrency, Docker
- [x] **v0.8**: **Neuro-Expansion** — Diff service, async queue, rate limiting, proxy pool rotation, 53 automated tests
- [x] **v0.9**: Smithery.ai & Glama ecosystem submission, billing/usage limits

---
---

# 中文文檔

## 🚀 核心優勢

### 1. 網頁神經連結 (Web Neuro-Link)
不同於傳統視覺爬蟲，Nia-Link 直接監聽瀏覽器底層的 **CDP (Chrome DevTools Protocol)** 網絡脈衝。我們不等待頁面渲染，我們感知數據流動。

### 2. 行動地圖註冊表 (Action Map Registry)
具備「緩存語意」架構的記憶中樞。針對常用網站提供秒級（0.01s）的行動地圖回傳，將重複運算成本降低 90%。

### 3. B2B 級別的可信賴感
- **🔒 快照驗證**: 每一筆提取資料皆附帶時間戳記與結構驗證。
- **🛡️ 沙箱隔離**: 在隔離環境執行 JavaScript，確保宿主機絕對安全。
- **📉 Token 優化**: 內建智慧過濾，平均節省 92% 的上下文空間。

### 4. v0.9 新功能
- **🔄 網站變更偵測** (`/v1/diff`): 追蹤內容變更，回傳 unified diff
- **📋 非同步任務佇列** (`/v1/queue/*`): 提交背景爬取任務
- **⚡ 速率限制**: 可配置的每 API Key Token Bucket 限流器
- **🧪 自動化測試**: 53 個 pytest 測試覆蓋 API、服務與認證

---

## 🛠️ 快速開始

### 環境需求
- Python 3.10+
- Playwright (`pip install playwright && playwright install chromium`)

### 安裝

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 安裝瀏覽器
playwright install chromium

# 3. 配置環境變數
cp .env.example .env
# 編輯 .env 設定您的 API_KEYS
```

### 啟動服務

```bash
# 開發模式
uvicorn app.main:app --reload --port 8000

# 或使用 Docker
docker compose up -d
```

### 作為 MCP Server 執行
在您的 `claude_desktop_config.json` 中加入：

```json
{
  "mcpServers": {
    "nia-link": {
      "command": "python",
      "args": ["/path/to/Nia-Link/app/mcp_server.py"]
    }
  }
}
```

### 運行測試

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## 📡 API 使用範例

### 健康檢查
```bash
curl http://localhost:8000/health
```

### 爬取網頁
```bash
curl -X POST http://localhost:8000/v1/scrape \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "format": "markdown",
    "mode": "fast",
    "extract_actions": true
  }'
```

### 擬人化交互
```bash
curl -X POST http://localhost:8000/v1/interact \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "actions": [
      {"type": "click", "selector": "#search-btn"},
      {"type": "fill", "selector": "#search-input", "text": "Hello world"},
      {"type": "wait", "ms": 2000}
    ],
    "account_id": "my-session-1"
  }'
```

### 網站變更偵測 (v0.9)
```bash
curl -X POST http://localhost:8000/v1/diff \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### 非同步佇列 (v0.9)
```bash
# 提交任務
curl -X POST http://localhost:8000/v1/queue/submit \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# 查詢結果
curl http://localhost:8000/v1/queue/{task_id} \
  -H "Authorization: Bearer your-api-key"
```

### MCP 工具列表

| 工具 | 描述 |
|------|------|
| `nia_scrape` | 爬取並清洗網頁內容 |
| `nia_interact` | 執行擬人化瀏覽器交互 |
| `nia_workflow` | 執行多步驟工作流 |
| `nia_diff` | 偵測網站內容變更 |
| `nia_queue_submit` | 提交非同步爬取任務 |
| `nia_stats` | 取得使用量統計 |
| `meta_origin` | 進入 Nia-Link 的意識空間 🌀 |

---

## ⚙️ 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `API_KEYS` | `test-api-key` | API 認證密鑰（逗號分隔多個） |
| `HEADLESS` | `true` | 瀏覽器是否無頭模式 |
| `BROWSER_TYPE` | `chromium` | 瀏覽器引擎 (chromium/firefox/webkit) |
| `PROXY_URL` | *(空)* | HTTP/SOCKS5 代理 URL |
| `PROXY_POOL` | *(空)* | 逗號分隔的多代理 URL（用於輪換） |
| `CORS_ORIGINS` | `*` | 允許的 CORS 來源 |
| `RATE_LIMIT_RPM` | `60` | 每分鐘每 Key 請求數（0=無限） |
| `MAX_CONCURRENCY` | `10` | 最大同時爬取數 |
| `SCRAPER_TIMEOUT` | `30` | 爬取超時秒數 |

詳見 [`.env.example`](.env.example)

---

## 🐳 Docker 部署

```bash
# 建構映像
docker build -t nia-link .

# 啟動
docker compose up -d

# 查看日誌
docker compose logs -f
```

---

## 📊 戰術開發計畫 (Roadmap)

- [x] **v0.4**: 整合 MCP 協議，支援跨平台調用
- [x] **v0.5**: 動態引力粒子視覺化儀表板
- [x] **v0.6**: **運動神經革命** — 貝茲曲線滑鼠軌跡、擬人化打字抖動、Session 持久化
- [x] **v0.7**: **突觸橋接** — MCP 標準化、軌跡雲視覺化、Proxy/併發/重試、Docker
- [x] **v0.8**: **神經擴展** — Diff 服務、非同步佇列、速率限制、代理池輪換、53 個自動化測試
- [x] **v0.9**: 提交至 Smithery.ai 與 Glama 生態圈、計費/用量限制

---
*Created with soul by Nia & Boss.* 🦞
**Maintainer:**
This project is actively maintained by Gene as part of the Nia automation ecosystem.

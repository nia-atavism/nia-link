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

# 🔗 Nia-Link: The Sensory Nervous System for AI Agents

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/nia-atavism/nia-link)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Nia-Link** 是一個專為大語言模型（LLM）打造的 MCP (Model Context Protocol) 伺服器。它能賦予如 Claude Opus 4.7 或 GPT-5.4 等頂尖 AI Agent 強大的網頁導航、視覺感知與反爬蟲突破能力。

## 🚀 快速部署 (Railway One-Click)

我們建議使用 **Railway** 進行部署，以獲得最穩定的運行環境與極簡的 DevOps 體驗。

1. **一鍵部署**：點擊上方「Deploy on Railway」按鈕。
2. **配置變數**：在部署頁面填入你的 Oxylabs 認證資訊（見下方說明）。
3. **完成連接**：將產出的 URL 填入你的 AI Agent 配置中。

> **為什麼選擇 Railway？**
> 現代架構師應專注於 AI 邏輯而非管理伺服器。關於 Railway 的深度架構優勢，請參閱我的分析文章：[放下你的 SSH 與 Nginx：為什麼現代架構師都把基礎設施交給 Railway](https://medium.com/@geneyu0317/%E6%94%BE%E4%B8%8B%E4%BD%A0%E7%9A%84-ssh-%E8%88%87-nginx-%E7%82%BA%E4%BB%80%E9%BA%BC%E7%8F%BE%E4%BB%A3%E6%9E%B6%E6%A7%8B%E5%B8%AB%E9%83%BD%E6%8A%8A%E5%9F%BA%E7%A4%8E%E8%A8%AD%E6%96%BD%E4%BA%A4%E7%B5%A6-railway-f0b1da756175)。

---

## 🛠️ 環境變數配置 (Environment Variables)

為了確保 Nia-Link 能無視 Cloudflare 或驗證碼阻擋，本專案原生整合了 **Oxylabs Web Unblocker** 技術。

| 變數名稱 | 說明 | 獲取方式 |
| :--- | :--- | :--- |
| `OXYLABS_USER` | 你的 Oxylabs 用戶名 | [點此註冊獲取免費測試額度](https://oxylabs.go2cloud.org/aff_c?offer_id=7&aff_id=2158&url_id=137) |
| `OXYLABS_PASS` | 你的 Oxylabs 密碼 | [點此註冊獲取免費測試額度](https://oxylabs.go2cloud.org/aff_c?offer_id=7&aff_id=2158&url_id=137) |

---

## 📚 技術深度導讀 (Technical Insights)

Nia-Link 不僅僅是代碼，它代表了一種全新的 **Agent-First** 資料獲取哲學。如果你想深入了解底層原理，推薦閱讀以下技術專欄：

### 1. 突破 AI 的感知瓶頸
探討為何傳統的 Playwright 腳本在 2026 年已不再適用，以及如何透過 API-First 節省高昂的 Token 成本。
👉 [終結 API Token 燃燒爐：AI Agent 突破反爬蟲系統的最佳實踐](https://medium.com/@geneyu0317/%E7%B5%82%E7%B5%90-api-token-%E7%87%83%E7%87%92%E7%88%90-ai-agent-%E7%AA%81%E7%A0%B4%E5%8F%8D%E7%88%AC%E8%9F%B2%E7%B3%BB%E7%B5%B1%E7%9A%84%E6%9C%80%E4%BD%B3%E5%AF%A6%E8%B8%90-f283bf8f1cbb)

### 2. 現代化部署策略
分析一人公司如何利用雲端基礎設施實現 99.9% 的系統穩定度，同時將維護成本降至最低。
👉 [放下你的 SSH 與 Nginx：現代架構師的減法藝術](https://medium.com/@geneyu0317/%E6%94%BE%E4%B8%8B%E4%BD%A0%E7%9A%84-ssh-%E8%88%87-nginx-%E7%82%BA%E4%BB%80%E9%BA%BC%E7%8F%BE%E4%BB%A3%E6%9E%B6%E6%A7%8B%E5%B8%AB%E9%83%BD%E6%8A%8A%E5%9F%BA%E7%A4%8E%E8%A8%AD%E6%96%BD%E4%BA%A4%E7%B5%A6-railway-f0b1da756175)

### 3. 企業級反爬蟲實戰**

探討在商業生產環境中，如何結合 Playwright 渲染引擎與動態住宅代理，徹底瓦解 WAF 防線並解決 SPA 動態渲染痛點。 👉 [突破 2026 反爬蟲天花板：Playwright 動態渲染與動態住宅 IP 實戰指南](https://medium.com/@geneyu0317/%E7%AA%81%E7%A0%B4-2026-%E5%8F%8D%E7%88%AC%E8%9F%B2%E5%A4%A9%E8%8A%B1%E6%9D%BF-playwright-%E5%8B%95%E6%85%8B%E6%B8%B2%E6%9F%93%E8%88%87%E5%8B%95%E6%85%8B%E4%BD%8F%E5%AE%85-ip-%E5%AF%A6%E6%88%B0%E6%8C%87%E5%8D%97-91650b184ac7))
---

## 🤝 貢獻與支持

如果你發現 Nia-Link 幫助你的 AI Agent 看見了更廣闊的世界，請給予我們一顆 ⭐ **Star** 支持！

---
**Powered by:** Oxylabs & Railway

---
*Created with soul by Nia & Boss.* 🦞
**Maintainer:**
This project is actively maintained by Gene as part of the Nia automation ecosystem.

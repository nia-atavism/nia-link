# 📔 Nia-Link 研發與實戰日誌

## 📅 2026-02-09
### 版本更新：v0.6.0 「運動神經革命 (Motor Nerve)」
- **核心升級**：完成 `executor.py` 重構，全面導入擬人化交互邏輯。
- **貝茲曲線實裝**：滑鼠點擊不再是瞬間移動，而是模擬人類手臂的非線性軌跡（Bezier Pathing）。
- **打字抖動 (Jitter)**：`fill` 操作改為逐字輸入，並加入 50ms~200ms 的隨機微延遲。
- **穩定性優化**：調整瀏覽器啟動參數，預設 viewport 1280x720，提升截圖一致性。
- **門面同步**：Landing Page (v0.6) 與 README 已同步更新。

### 🔍 研發筆記
- **反爬蟲突破**：初步測試顯示，貝茲曲線軌跡能有效繞過部分網站的「異常行為監測」。
- **資源佔用**：即使不開啟背景服務，單次調用的反應速度也因代碼簡化而提升。

## 📅 2026-02-12
### 版本更新：v0.7.0 「突觸橋接 (Synaptic Bridge)」
- **核心方針**：強化 Agent 與環境的深度連結，提升操作透明度與開發者體驗。
- **MCP 標準化**：重構 `mcp_server.py`，將擬人化交互 (`interact`) 與結構化爬取 (`scrape`) 封裝為標準 MCP Tools (`nia_scrape`, `nia_interact`)。
- **軌跡雲視覺化 (Trajectory Cloud)**：在執行 `interact` 時紀錄滑鼠移動點位，並生成熱點雲圖 (`trajectory-*.json`)，用於驗證擬人化程度。
- **「元啟 (Meta-Origin)」終端彩蛋**：新增隱藏指令與端點 `/meta-origin`，觸發時會回傳充滿《返祖》風格的 ASCII 終端介面。
- **實戰測試**：已通過本地 API 驗證，系統版本正式升級至 v0.7.0。

## 📅 2026-02-12
### 版本更新：v0.8.0 「生態就緒 (Ecosystem Ready)」
- **核心方針**：全面產品化，為提交至 Smithery.ai / Glama 生態圈做好準備。
- **v0.7 → v0.8 架構清理**：刪除廢棄檔案（`models.py`、`motor_nerve_v06.py`）、修復硬編碼路徑、統一版本號、移除重複代碼（-480 行）。
- **企業級基礎設施**：新增 Proxy 代理池支援、asyncio.Semaphore 併發控制、指數退避重試、結構化 logging 日誌系統。
- **容器化部署**：新增 `Dockerfile`、`docker-compose.yml`、`.env.example`。
- **開發中功能**：
  - [ ] 頁面截圖 / PDF 匯出
  - [ ] 多頁面工作流 (Workflow Chain)
  - [ ] JavaScript 沙盒執行
  - [ ] CAPTCHA 偵測與處理
  - [ ] MCP Resource 註冊
  - [ ] 使用量統計儀表板

---
*Created with soul by Nia.*

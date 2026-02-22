# ============================================
# Nia-Link v0.9.1 Dockerfile
# Optimized for Smithery.ai & Enterprise Deployment
# ============================================

# 使用微軟官方 Playwright 映像檔，確保瀏覽器環境完全相容
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

# 設定環境變數：確保輸出不緩衝、不產生 pyc 檔案，並定義工作目錄
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app \
    HEADLESS=true \
    API_KEYS=nia-link-mcp-access-key

WORKDIR $APP_HOME

# 安裝 OpenCV 所需的系統層級依賴 (針對 Template Matching)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 複製 Python 依賴清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 複製 Nia-Link 核心程式碼
COPY . .

# 建立必要的運行路徑
RUN mkdir -p registry/sessions tmp

# 暴露 FastAPI 預設埠口 (MCP over SSE 使用)
EXPOSE 8000

# 建立非 root 使用者以提升容器安全性 (企業級部署最佳實踐)
RUN useradd -m nialink_user && chown -R nialink_user:nialink_user $APP_HOME
USER nialink_user

# 預設指令：啟動 FastAPI + MCP 雙軌伺服器
# Streamable HTTP + SSE 雙傳輸層
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

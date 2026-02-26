# 1. 選擇輕量級的 Python 3.11 作為基底
FROM python:3.11-slim

# 設定容器內的工作目錄
WORKDIR /app

# 2. 安裝基礎系統依賴 (git 是為了某些依賴安裝，libgl1 等是為了可能的影像處理)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. 複製依賴清單並安裝基礎 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. 【一擊必殺的核心】安裝 Playwright 及其深層作業系統依賴
# 先安裝 Chromium 瀏覽器本體
RUN playwright install chromium
# 再強制安裝所有 Ubuntu/Debian 系統級的依賴 (字型、共享庫等)
RUN playwright install-deps chromium

# 5. 將你所有的後端程式碼複製進容器
COPY . .

# 6. 暴露 Railway 預設分配的 Port
EXPOSE 8000

# 7. 啟動 FastAPI 伺服器
# 使用 sh -c 來確保環境變數 PORT 正確注入
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

import asyncio
import aiohttp
import time

# 測試目標配置：對應 Nia-Link v0.9 的真實路徑
TARGET_URL = "http://localhost:8000/v1/scrape"
CONCURRENT_REQUESTS = 5 
TOTAL_REQUESTS = 20 

# 模擬觸發 WebMCP Sniffer 
PAYLOAD = {
    "url": "https://www.google.com",
    "mode": "visual",
    "format": "markdown",
    "extract_actions": True
}

# 認證密鑰
HEADERS = {
    "Authorization": "Bearer nia-link-mcp-access-key",
    "Content-Type": "application/json"
}

async def fetch(session, request_id):
    """發送單一請求並記錄反應時間"""
    start_time = time.time()
    try:
        async with session.post(TARGET_URL, json=PAYLOAD, headers=HEADERS, timeout=120) as response:
            status = response.status
            await response.text()
            elapsed = time.time() - start_time
            print(f"[任務 {request_id}] 狀態碼: {status} | 耗時: {elapsed:.2f} 秒")
            return status, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[任務 {request_id}] 失敗: {str(e)} | 耗時: {elapsed:.2f} 秒")
        return "ERROR", elapsed

async def bound_fetch(sem, session, request_id):
    """使用 Semaphore 控制最大併發量"""
    async with sem:
        return await fetch(session, request_id)

async def main():
    print(f"🚀 啟動 Nia-Link 神經壓力測試...")
    print(f"目標端點: {TARGET_URL}")
    print(f"最大併發數: {CONCURRENT_REQUESTS} | 總請求數: {TOTAL_REQUESTS}")
    
    start_all = time.time()
    sem = asyncio.Semaphore(CONCURRENT_REQUESTS)
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(TOTAL_REQUESTS):
            task = asyncio.ensure_future(bound_fetch(sem, session, i + 1))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)

    # 統計測試結果
    successful = sum(1 for r in results if r[0] == 200)
    failed = TOTAL_REQUESTS - successful
    total_time = time.time() - start_all
    
    print("\n" + "="*30)
    print(" 📊 Nia-Link 壓力測試報告")
    print("="*30)
    print(f"總執行時間: {total_time:.2f} 秒")
    print(f"成功請求數: {successful}")
    print(f"失敗/超時數: {failed}")
    if successful > 0:
        avg_time = sum(r[1] for r in results if r[0] == 200) / successful
        print(f"平均成功耗時: {avg_time:.2f} 秒")
    print("="*30)

if __name__ == "__main__":
    asyncio.run(main())

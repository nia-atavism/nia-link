
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def debug_railway():
    executor = ExecutorService(headless=False)
    
    url = "https://railway.com/dashboard"
    
    actions = [
        {"type": "wait", "ms": 5000},
        # 點擊專案進入詳情頁面（假設它是清單中的第一個）
        {"type": "click", "selector": "a:has-text('Nia-Link_v0.9')", "label": "Enter Project"},
        {"type": "wait", "ms": 3000},
        # 檢查佈署狀態和 Log
        {"type": "click", "selector": "button:has-text('Deployments')", "label": "Check Deployments"},
        {"type": "wait", "ms": 5000},
    ]
    
    print("Checking Railway deployment status...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        print("Status check completed.")
        with open("debug_railway_status.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
    else:
        print(f"Failed to check status: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(debug_railway())

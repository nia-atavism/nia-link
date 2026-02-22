
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def fix_and_get_url():
    executor = ExecutorService(headless=False)
    
    url = "https://railway.com/dashboard"
    
    actions = [
        {"type": "wait", "ms": 10000}, # 給更多時間載入
        {"type": "click", "selector": "a:has-text('Nia-Link_v0.9')", "label": "Enter Project"},
        {"type": "wait", "ms": 5000},
        # 尋找具體的服務卡片並點擊
        {"type": "click", "selector": "div[role='button']:has-text('Nia-Link')", "label": "Select Service"},
        {"type": "wait", "ms": 3000},
        {"type": "click", "selector": "button:has-text('Settings')", "label": "Settings"},
        {"type": "wait", "ms": 5000},
        # 截圖確認 Settings 頁面
    ]
    
    print("Repairing Railway networking and fetching URL...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        print("Settings page accessed.")
        with open("fix_railway_status.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
    else:
        print(f"Failed to access settings: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(fix_and_get_url())

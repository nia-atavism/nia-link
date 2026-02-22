
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def get_real_url():
    executor = ExecutorService(headless=False)
    
    url = "https://railway.com/dashboard"
    
    actions = [
        {"type": "wait", "ms": 5000},
        {"type": "click", "selector": "a:has-text('Nia-Link_v0.9')", "label": "Enter Project"},
        {"type": "wait", "ms": 3000},
        {"type": "click", "selector": "button:has-text('Settings')", "label": "Settings"},
        {"type": "wait", "ms": 3000},
        # 尋找網域相關資訊
    ]
    
    print("Fetching real deployment URL...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        print("URL fetch completed.")
        with open("railway_url_check.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
    else:
        print(f"Failed to fetch URL: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(get_real_url())

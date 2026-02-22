
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def hard_reset_networking():
    executor = ExecutorService(headless=True)
    url = "https://railway.com/dashboard"
    
    actions = [
        {"type": "wait", "ms": 10000},
        {"type": "click", "selector": "a:has-text('Nia-Link_v0.9')", "label": "Enter Project"},
        {"type": "wait", "ms": 5000},
        {"type": "click", "selector": "div[role='button']:has-text('Nia-Link')", "label": "Select Service"},
        {"type": "wait", "ms": 3000},
        {"type": "click", "selector": "button:has-text('Settings')", "label": "Settings"},
        {"type": "wait", "ms": 5000},
        {"type": "scroll", "direction": "down", "amount": 1000},
        {"type": "wait", "ms": 2000},
        # 這裡需要找到 Remove 舊網域並 Generate New 的操作
        {"type": "click", "selector": "button[aria-label='Domain Options']", "label": "Domain Options"},
        {"type": "wait", "ms": 1000},
        {"type": "click", "selector": "button:has-text('Remove')", "label": "Remove Domain"},
        {"type": "wait", "ms": 2000},
        {"type": "click", "selector": "button:has-text('Generate Domain')", "label": "Generate New Domain"},
        {"type": "wait", "ms": 5000},
    ]
    
    print("Hard resetting networking domains...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        with open("networking_reset_result.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
        print("Reset sequence complete.")
    else:
        print(f"Failed: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(hard_reset_networking())

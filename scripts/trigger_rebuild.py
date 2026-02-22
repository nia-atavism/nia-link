
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def trigger_rebuild_and_fix():
    executor = ExecutorService(headless=True)
    url = "https://railway.com/dashboard"
    
    actions = [
        {"type": "wait", "ms": 10000},
        {"type": "click", "selector": "a:has-text('Nia-Link_v0.9')", "label": "Enter Project"},
        {"type": "wait", "ms": 5000},
        {"type": "click", "selector": "div[role='button']:has-text('Nia-Link')", "label": "Select Service"},
        {"type": "wait", "ms": 3000},
        {"type": "click", "selector": "button:has-text('Deployments')", "label": "Deployments"},
        {"type": "wait", "ms": 3000},
        # 尋找最新的 Deployment 並點擊 Redeploy 或重新觸發
        {"type": "click", "selector": "button:has-text('Redeploy')", "label": "Redeploy"},
        {"type": "wait", "ms": 5000},
    ]
    
    print("Triggering forced rebuild and fix...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        print("Rebuild triggered.")
        with open("rebuild_triggered.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
    else:
        print(f"Failed: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(trigger_rebuild_and_fix())

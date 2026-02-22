
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def deploy_railway():
    executor = ExecutorService(headless=False)
    
    # 1. 前往 Railway Dashboard
    url = "https://railway.com/dashboard"
    
    # 2. 點擊 "New Project" -> "Deploy from GitHub repo"
    # 注意：這裡假設已經登入（使用 railway-nia session）
    actions = [
        {"type": "wait", "ms": 5000},
        {"type": "click", "selector": "button:has-text('New Project')", "label": "New Project"},
        {"type": "wait", "ms": 2000},
        {"type": "click", "selector": "button:has-text('GitHub Repo')", "label": "GitHub Repo"},
        {"type": "wait", "ms": 2000},
        {"type": "click", "selector": "div:has-text('nia-atavism/Nia-Link_v0.9')", "label": "Select Repo"},
        {"type": "wait", "ms": 2000},
        {"type": "click", "selector": "button:has-text('Deploy Now')", "label": "Deploy Now"},
        {"type": "wait", "ms": 10000},
    ]
    
    print("Starting deployment via Nia-Link...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        print("Success! Deployment initiated.")
        with open("deployment_result.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
    else:
        print(f"Failed: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(deploy_railway())

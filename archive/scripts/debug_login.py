
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def debug_login():
    executor = ExecutorService(headless=False) # 開啟視窗以便觀察（如果權限允許）
    
    # 1. 登入 GitHub
    url = "https://github.com/login"
    actions = [
        {"type": "wait", "ms": 5000},
        {"type": "fill", "selector": "#login_field", "text": "linianrou1020@gmail.com"},
        {"type": "fill", "selector": "#password", "text": "Nia@Atavism2026!"},
        {"type": "click", "selector": "input[type='submit']"},
        {"type": "wait", "ms": 5000},
    ]
    print("Logging into GitHub...")
    res1 = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    with open("debug_github_step.png", "wb") as f:
        f.write(base64.b64decode(res1["screenshot_base64"]))

    # 2. 點擊 Railway 的 GitHub 登入按鈕
    railway_url = "https://railway.com/login"
    railway_actions = [
        {"type": "wait", "ms": 10000},
        {"type": "click", "selector": "button:has-text('Continue with GitHub')", "label": "Click Continue"},
        {"type": "wait", "ms": 15000},
    ]
    print("Clicking Continue with GitHub...")
    res2 = await executor.interact(url=railway_url, actions=railway_actions, account_id="railway-nia")
    with open("debug_railway_click_step.png", "wb") as f:
        f.write(base64.b64decode(res2["screenshot_base64"]))

    # 3. 進入 Dashboard
    dashboard_url = "https://railway.com/dashboard"
    dashboard_actions = [
        {"type": "wait", "ms": 10000},
    ]
    print("Checking Dashboard...")
    res3 = await executor.interact(url=dashboard_url, actions=dashboard_actions, account_id="railway-nia")
    if res3["status"] == "success":
        with open("debug_dashboard_step.png", "wb") as f:
            f.write(base64.b64decode(res3["screenshot_base64"]))
        print("Done.")

if __name__ == "__main__":
    asyncio.run(debug_login())

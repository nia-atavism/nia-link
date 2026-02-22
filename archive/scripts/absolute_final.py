
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def final_attempt():
    executor = ExecutorService(headless=True)
    
    # 1. 登入 GitHub 以確保 Railway Session 有效
    github_url = "https://github.com/login"
    github_actions = [
        {"type": "wait", "ms": 5000},
        {"type": "fill", "selector": "#login_field", "text": "linianrou1020@gmail.com"},
        {"type": "fill", "selector": "#password", "text": "Nia@Atavism2026!"},
        {"type": "click", "selector": "input[type='submit']"},
        {"type": "wait", "ms": 5000},
    ]
    print("Logging into GitHub...")
    await executor.interact(url=github_url, actions=github_actions, account_id="railway-nia")

    # 2. 登入 Railway
    railway_url = "https://railway.com/login"
    railway_actions = [
        {"type": "wait", "ms": 10000},
        {"type": "click", "selector": "button:has-text('GitHub')", "label": "GitHub Login"},
        {"type": "wait", "ms": 10000},
    ]
    print("Logging into Railway...")
    await executor.interact(url=railway_url, actions=railway_actions, account_id="railway-nia")

    # 3. 進入專案 Settings 獲取網址
    dashboard_url = "https://railway.com/dashboard"
    dashboard_actions = [
        {"type": "wait", "ms": 15000},
        {"type": "click", "selector": "a:has-text('Nia-Link_v0.9')", "label": "Enter Project"},
        {"type": "wait", "ms": 5000},
        {"type": "click", "selector": "div[role='button']:has-text('Nia-Link')", "label": "Select Service"},
        {"type": "wait", "ms": 3000},
        {"type": "click", "selector": "button:has-text('Settings')", "label": "Settings"},
        {"type": "wait", "ms": 5000},
        {"type": "scroll", "direction": "down", "amount": 1000},
        {"type": "wait", "ms": 5000},
    ]
    print("Accessing Railway Dashboard...")
    dash_result = await executor.interact(url=dashboard_url, actions=dashboard_actions, account_id="railway-nia")
    
    if dash_result["status"] == "success":
        with open("absolute_final_check.png", "wb") as f:
            f.write(base64.b64decode(dash_result["screenshot_base64"]))
        print("SUCCESS: Absolute final check saved.")
    else:
        print(f"FAILED: {dash_result.get('message')}")

if __name__ == "__main__":
    asyncio.run(final_attempt())

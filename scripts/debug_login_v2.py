
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def debug_login_v2():
    executor = ExecutorService(headless=True)
    
    # 1. 前往 GitHub 登入頁面
    print("Step 1: Navigating to GitHub Login...")
    url = "https://github.com/login"
    actions = [
        {"type": "wait", "ms": 5000},
        {"type": "fill", "selector": "#login_field", "text": "linianrou1020@gmail.com"},
        {"type": "fill", "selector": "#password", "text": "Nia@Atavism2026!"},
        {"type": "click", "selector": "input[type='submit']"},
        {"type": "wait", "ms": 10000}, # 等待 2FA 或跳轉
    ]
    res1 = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    with open("v2_debug_github_login.png", "wb") as f:
        f.write(base64.b64decode(res1["screenshot_base64"]))
    print(f"Step 1 log: {res1['log']}")

    # 2. 如果成功進入 GitHub，嘗試前往 Railway
    print("Step 2: Navigating to Railway Login...")
    railway_url = "https://railway.com/login"
    railway_actions = [
        {"type": "wait", "ms": 10000},
        {"type": "click", "selector": "button:has-text('GitHub')", "label": "Continue with GitHub"},
        {"type": "wait", "ms": 15000},
    ]
    res2 = await executor.interact(url=railway_url, actions=railway_actions, account_id="railway-nia")
    with open("v2_debug_railway_auth.png", "wb") as f:
        f.write(base64.b64decode(res2["screenshot_base64"]))
    print(f"Step 2 log: {res2['log']}")

    # 3. 檢查是否進入 Dashboard 並尋找網址
    print("Step 3: Checking Railway Dashboard...")
    dashboard_url = "https://railway.com/dashboard"
    dashboard_actions = [
        {"type": "wait", "ms": 10000},
        {"type": "click", "selector": "a:has-text('Nia-Link_v0.9')", "label": "Enter Project"},
        {"type": "wait", "ms": 5000},
        {"type": "click", "selector": "div[role='button']:has-text('Nia-Link')", "label": "Select Service"},
        {"type": "wait", "ms": 3000},
        {"type": "click", "selector": "button:has-text('Settings')", "label": "Settings"},
        {"type": "wait", "ms": 5000},
        {"type": "scroll", "direction": "down", "amount": 1000},
        {"type": "wait", "ms": 5000},
    ]
    res3 = await executor.interact(url=dashboard_url, actions=dashboard_actions, account_id="railway-nia")
    if res3["status"] == "success":
        with open("v2_absolute_final_check.png", "wb") as f:
            f.write(base64.b64decode(res3["screenshot_base64"]))
        print("SUCCESS: V2 Absolute final check saved.")
    else:
        print(f"FAILED: {res3.get('message')}")

if __name__ == "__main__":
    asyncio.run(debug_login_v2())

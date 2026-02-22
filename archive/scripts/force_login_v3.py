
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def force_login_v3():
    executor = ExecutorService(headless=True)
    
    # 1. 確保 GitHub 登入成功
    print("Step 1: Logging into GitHub...")
    github_url = "https://github.com/login"
    github_actions = [
        {"type": "wait", "ms": 5000},
        {"type": "fill", "selector": "#login_field", "text": "linianrou1020@gmail.com"},
        {"type": "fill", "selector": "#password", "text": "Nia@Atavism2026!"},
        {"type": "click", "selector": "input[type='submit']"},
        {"type": "wait", "ms": 10000},
    ]
    res1 = await executor.interact(url=github_url, actions=github_actions, account_id="railway-nia")
    print(f"Step 1 finished. Log: {res1['log']}")

    # 2. 進入 Railway Login
    print("Step 2: Entering Railway Login...")
    railway_url = "https://railway.com/login"
    railway_actions = [
        {"type": "wait", "ms": 10000},
        {"type": "click", "selector": "button:has-text('Continue with GitHub')", "label": "GitHub Auth"},
        {"type": "wait", "ms": 15000}, # 增加等待時間，因為 OAuth 跳轉很慢
    ]
    res2 = await executor.interact(url=railway_url, actions=railway_actions, account_id="railway-nia")
    with open("v3_debug_after_railway_click.png", "wb") as f:
        f.write(base64.b64decode(res2["screenshot_base64"]))
    print(f"Step 2 finished. Log: {res2['log']}")

    # 3. 如果沒跳轉，可能需要點擊 GitHub 的 Authorize 按鈕
    # 但我們先檢查 dashboard
    print("Step 3: Checking Dashboard directly...")
    dashboard_url = "https://railway.com/dashboard"
    dashboard_actions = [
        {"type": "wait", "ms": 10000},
    ]
    res3 = await executor.interact(url=dashboard_url, actions=dashboard_actions, account_id="railway-nia")
    with open("v3_debug_dashboard_final.png", "wb") as f:
        f.write(base64.b64decode(res3["screenshot_base64"]))
    
    if res3["status"] == "success":
        print("Final check on V3 done.")

if __name__ == "__main__":
    asyncio.run(force_login_v3())

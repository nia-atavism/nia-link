
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def debug_oauth_step():
    executor = ExecutorService(headless=True)
    
    # 1. 確保 GitHub 登入成功
    print("Step 1: Logging into GitHub...")
    github_url = "https://github.com/login"
    github_actions = [
        {"type": "wait", "ms": 5000},
        {"type": "fill", "selector": "#login_field", "text": "linianrou1020@gmail.com"},
        {"type": "fill", "selector": "#password", "text": "Nia@Atavism2026!"},
        {"type": "click", "selector": "input[type='submit']"},
        {"type": "wait", "ms": 5000},
    ]
    await executor.interact(url=github_url, actions=github_actions, account_id="railway-nia")

    # 2. 點擊 Railway 的 GitHub 登入
    print("Step 2: Clicking Continue with GitHub on Railway...")
    railway_url = "https://railway.com/login"
    railway_actions = [
        {"type": "wait", "ms": 5000},
        {"type": "click", "selector": "button:has-text('Continue with GitHub')", "label": "GitHub Auth"},
        {"type": "wait", "ms": 10000},
    ]
    res2 = await executor.interact(url=railway_url, actions=railway_actions, account_id="railway-nia")
    with open("oauth_step_check.png", "wb") as f:
        f.write(base64.b64decode(res2["screenshot_base64"]))
    
    # 3. 檢查目前是否停在 GitHub 的授權頁面，如果是，點擊授權
    # 這一步很關鍵，因為雖然我們登入了 GitHub，但如果是第一次或 Session 過期，GitHub 會要求點擊 Authorize
    print("Step 3: Checking if Authorize button exists...")
    auth_actions = [
        {"type": "wait", "ms": 5000},
        {"type": "click", "selector": "button:has-text('Authorize')", "label": "Authorize Railway"},
        {"type": "wait", "ms": 10000},
    ]
    # 我們不更換 URL，直接在目前頁面操作（如果已經跳轉到 GitHub Auth）
    # 但 executor 每次調用都會打開新頁面，所以這裏我們需要把動作合併
    
if __name__ == "__main__":
    # 為了保持 Session，我們把動作合併到一個流程中
    async def merged_flow():
        executor = ExecutorService(headless=True)
        print("Starting Merged Auth Flow...")
        
        # 合併所有動作到一個 URL 引發的連鎖反應中
        url = "https://github.com/login"
        actions = [
            {"type": "wait", "ms": 5000},
            {"type": "fill", "selector": "#login_field", "text": "linianrou1020@gmail.com"},
            {"type": "fill", "selector": "#password", "text": "Nia@Atavism2026!"},
            {"type": "click", "selector": "input[type='submit']"},
            {"type": "wait", "ms": 5000},
            {"type": "evaluate", "script": "window.location.href = 'https://railway.com/login'"},
            {"type": "wait", "ms": 10000},
            {"type": "click", "selector": "button:has-text('Continue with GitHub')"},
            {"type": "wait", "ms": 10000},
            # 此時可能跳轉到 GitHub Authorize 或直接進入 Dashboard
            {"type": "click", "selector": "button:has-text('Authorize')", "label": "Authorize if exists"},
            {"type": "wait", "ms": 10000},
            # 最後檢查網址，看有沒有進入 Dashboard
            {"type": "evaluate", "script": "window.location.href = 'https://railway.com/dashboard'"},
            {"type": "wait", "ms": 10000},
        ]
        
        res = await executor.interact(url=url, actions=actions, account_id="railway-nia")
        with open("merged_auth_final_check.png", "wb") as f:
            f.write(base64.b64decode(res["screenshot_base64"]))
        print(f"Merged flow log: {res['log']}")

    asyncio.run(merged_flow())

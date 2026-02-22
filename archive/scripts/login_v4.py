
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def login_v4():
    executor = ExecutorService(headless=True)
    
    # 1. 登入 GitHub
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

    # 2. 進入 Railway 並點擊 GitHub 登入
    # 我將使用 JavaScript 直接點擊按鈕，規避 selector 找不到的問題
    railway_url = "https://railway.com/login"
    print("Step 2: Clicking Continue with GitHub via JS...")
    railway_actions = [
        {"type": "wait", "ms": 10000},
        {"type": "evaluate", "script": """
            const buttons = Array.from(document.querySelectorAll('button'));
            const githubBtn = buttons.find(b => b.textContent.includes('Continue with GitHub'));
            if (githubBtn) {
                githubBtn.click();
            } else {
                throw new Error('GitHub button not found');
            }
        """},
        {"type": "wait", "ms": 15000},
    ]
    res2 = await executor.interact(url=railway_url, actions=railway_actions, account_id="railway-nia")
    with open("v4_debug_step2.png", "wb") as f:
        f.write(base64.b64decode(res2["screenshot_base64"]))

    # 3. 檢查 Authorize
    print("Step 3: Checking for Authorize button...")
    auth_actions = [
        {"type": "evaluate", "script": """
            const buttons = Array.from(document.querySelectorAll('button'));
            const authBtn = buttons.find(b => b.textContent.includes('Authorize'));
            if (authBtn) {
                authBtn.click();
            }
        """},
        {"type": "wait", "ms": 10000},
    ]
    # 我們再次在同一個 Session 中操作
    res3 = await executor.interact(url="https://github.com", actions=auth_actions, account_id="railway-nia")
    
    # 4. 最後檢查 Dashboard
    print("Step 4: Final check...")
    res4 = await executor.interact(url="https://railway.com/dashboard", actions=[{"type": "wait", "ms": 10000}], account_id="railway-nia")
    with open("v4_final_check.png", "wb") as f:
        f.write(base64.b64decode(res4["screenshot_base64"]))
    print("V4 process finished.")

if __name__ == "__main__":
    asyncio.run(login_v4())

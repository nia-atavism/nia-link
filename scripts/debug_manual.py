
import asyncio
import sys
import base64
import os
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def debug_login_manual():
    # Use a fresh ID to avoid session corruption
    session_id = f"debug-manual-{int(asyncio.get_event_loop().time())}"
    executor = ExecutorService(headless=True)
    
    # 1. 登入 GitHub
    print(f"Step 1: Logging into GitHub (Session: {session_id})...")
    github_url = "https://github.com/login"
    github_actions = [
        {"type": "wait", "ms": 5000},
        {"type": "fill", "selector": "#login_field", "text": "linianrou1020@gmail.com"},
        {"type": "fill", "selector": "#password", "text": "Nia@Atavism2026!"},
        {"type": "click", "selector": "input[type='submit']"},
        {"type": "wait", "ms": 10000},
    ]
    res1 = await executor.interact(url=github_url, actions=github_actions, account_id=session_id)
    with open("m_debug_step1_github.png", "wb") as f:
        f.write(base64.b64decode(res1["screenshot_base64"]))
    print(f"Log 1: {res1['log']}")

    # 2. 進入 Railway
    print("Step 2: Entering Railway...")
    railway_url = "https://railway.com/login"
    # 直接在 JS 裡檢查狀態並點擊
    railway_actions = [
        {"type": "wait", "ms": 10000},
        {"type": "evaluate", "script": """
            console.log("Current URL:", window.location.href);
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Continue with GitHub'));
            if (btn) {
                console.log("Found button, clicking...");
                btn.click();
                return "Clicked";
            }
            return "Button Not Found";
        """},
        {"type": "wait", "ms": 15000},
    ]
    res2 = await executor.interact(url=railway_url, actions=railway_actions, account_id=session_id)
    with open("m_debug_step2_railway.png", "wb") as f:
        f.write(base64.b64decode(res2["screenshot_base64"]))
    print(f"Log 2: {res2['log']}")
    print(f"JS Result 2: {res2.get('js_results')}")

    # 3. 檢查跳轉
    print("Step 3: Checking final destination...")
    dashboard_url = "https://railway.com/dashboard"
    res3 = await executor.interact(url=dashboard_url, actions=[{"type": "wait", "ms": 10000}], account_id=session_id)
    with open("m_debug_step3_dashboard.png", "wb") as f:
        f.write(base64.b64decode(res3["screenshot_base64"]))
    print(f"Log 3: {res3['log']}")

if __name__ == "__main__":
    asyncio.run(debug_login_manual())

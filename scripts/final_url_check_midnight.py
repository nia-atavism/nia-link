
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def login_and_get_url():
    executor = ExecutorService(headless=True)
    
    # 嘗試重新登入以恢復 Session
    url = "https://railway.com/login"
    actions = [
        {"type": "wait", "ms": 10000},
        {"type": "click", "selector": "button:has-text('GitHub')", "label": "GitHub Login"},
        {"type": "wait", "ms": 5000},
        # 假設已經在 GitHub 登入狀態，可能會自動跳轉
        {"type": "wait", "ms": 5000},
    ]
    
    print("Re-logging into Railway...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    # 進入 Dashboard
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
    
    print("Navigating to dashboard to find URL...")
    dash_result = await executor.interact(url=dashboard_url, actions=dashboard_actions, account_id="railway-nia")
    
    if dash_result["status"] == "success":
        with open("final_url_check_midnight.png", "wb") as f:
            f.write(base64.b64decode(dash_result["screenshot_base64"]))
        print("Success! Final screenshot captured.")
    else:
        print(f"Failed: {dash_result.get('message')}")

if __name__ == "__main__":
    asyncio.run(login_and_get_url())

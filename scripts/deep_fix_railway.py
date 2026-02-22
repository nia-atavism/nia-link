
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def deep_fix_railway():
    executor = ExecutorService(headless=True)
    url = "https://railway.com/dashboard"
    
    actions = [
        {"type": "wait", "ms": 10000},
        {"type": "click", "selector": "a:has-text('Nia-Link_v0.9')", "label": "Enter Project"},
        {"type": "wait", "ms": 5000},
        {"type": "click", "selector": "div[role='button']:has-text('Nia-Link')", "label": "Select Service"},
        {"type": "wait", "ms": 3000},
        {"type": "click", "selector": "button:has-text('Settings')", "label": "Settings"},
        {"type": "wait", "ms": 5000},
        {"type": "scroll", "direction": "down", "amount": 1200},
        {"type": "wait", "ms": 5000},
        # 捕捉 Settings 頁面中 Networking 的關鍵區域
    ]
    
    print("Executing deep diagnostic and screenshot...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        with open("deep_networking_diagnostic.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
        print("Diagnostic screenshot saved.")
        
        # 額外嘗試獲取 Deployments 的 Log 以確認容器內部是否真的啟動成功
        log_actions = [
             {"type": "wait", "ms": 2000},
             {"type": "click", "selector": "button:has-text('Deployments')", "label": "Go to Deployments"},
             {"type": "wait", "ms": 5000},
        ]
        log_result = await executor.interact(url="https://railway.com/dashboard", actions=log_actions, account_id="railway-nia")
        if log_result["status"] == "success":
             with open("railway_logs_check.png", "wb") as f:
                 f.write(base64.b64decode(log_result["screenshot_base64"]))
             print("Logs screenshot saved.")
    else:
        print(f"Failed: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(deep_fix_railway())

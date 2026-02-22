
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def complete_verification(code):
    executor = ExecutorService(headless=True)
    
    # 1. 進入 GitHub 驗證頁面並輸入代碼
    url = "https://github.com/sessions/verified-device"
    actions = [
        {"type": "wait", "ms": 5000},
        {"type": "fill", "selector": "#otp", "text": code},
        {"type": "click", "selector": "button:has-text('Verify')", "label": "Verify Button"},
        {"type": "wait", "ms": 10000},
    ]
    
    print(f"Entering code {code} into GitHub...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        with open("verify_success.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
        print("GitHub verification step completed.")
        
        # 2. 進入 Railway 並完成授權
        railway_url = "https://railway.com/login"
        railway_actions = [
            {"type": "wait", "ms": 10000},
            {"type": "click", "selector": "button:has-text('GitHub')", "label": "Railway GitHub Login"},
            {"type": "wait", "ms": 15000},
        ]
        print("Completing Railway OAuth...")
        rw_result = await executor.interact(url=railway_url, actions=railway_actions, account_id="railway-nia")
        
        if rw_result["status"] == "success":
            with open("railway_auth_final.png", "wb") as f:
                f.write(base64.b64decode(rw_result["screenshot_base64"]))
            print("Railway OAuth finished.")
        else:
            print(f"Railway OAuth failed: {rw_result.get('message')}")
    else:
        print(f"GitHub Verification failed: {result.get('message')}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(complete_verification(sys.argv[1]))
    else:
        print("No code provided.")

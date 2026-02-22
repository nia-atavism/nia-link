
import asyncio
import sys
import base64
import os
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def check_github_status():
    executor = ExecutorService(headless=True)
    
    # 檢查是否還在驗證碼頁面
    url = "https://github.com/sessions/verified-device"
    actions = [
        {"type": "wait", "ms": 5000},
        {"type": "evaluate", "script": "document.body.innerText"},
    ]
    
    print("Checking GitHub device verification status...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        text = result.get("js_results", [{}])[0].get("result", "")
        with open("github_verify_status.txt", "w") as f:
            f.write(text)
        print("Status saved.")
        with open("github_verify_screenshot.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
    else:
        # 可能已經登入成功或是其他頁面
        url2 = "https://github.com/settings/profile"
        result2 = await executor.interact(url=url2, actions=actions, account_id="railway-nia")
        with open("github_profile_check.png", "wb") as f:
            f.write(base64.b64decode(result2["screenshot_base64"]))
        print("Profile check saved.")

if __name__ == "__main__":
    asyncio.run(check_github_status())

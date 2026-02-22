
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def get_github_code():
    # 使用 linianrou1020@gmail.com 的 Session
    # 如果 OpenClaw 有 Google OAuth 權限，可能已經登入了
    executor = ExecutorService(headless=True)
    
    url = "https://mail.google.com/mail/u/0/#inbox"
    actions = [
        {"type": "wait", "ms": 15000},
        {"type": "evaluate", "script": "document.body.innerText"},
    ]
    
    print("Checking Gmail for GitHub code...")
    result = await executor.interact(url=url, actions=actions, account_id="google-nia") # 假設有這個 session
    
    if result["status"] == "success":
        text = result.get("js_results", [{}])[0].get("result", "")
        with open("gmail_dump.txt", "w") as f:
            f.write(text)
        print("Gmail dump saved.")
        with open("gmail_screenshot.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
    else:
        print(f"Failed: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(get_github_code())

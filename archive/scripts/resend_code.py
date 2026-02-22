
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def resend_github_code():
    executor = ExecutorService(headless=True)
    
    url = "https://github.com/sessions/verified-device"
    actions = [
        {"type": "wait", "ms": 5000},
        {"type": "click", "selector": "button:has-text('Re-send the authentication code')", "label": "Resend Code"},
        {"type": "wait", "ms": 5000},
    ]
    
    print("Resending GitHub verification code...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        with open("resend_screenshot.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
        print("Code resent successfully.")
    else:
        print(f"Failed to resend: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(resend_github_code())

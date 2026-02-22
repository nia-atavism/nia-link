
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def inspect_railway_login():
    executor = ExecutorService(headless=True)
    
    url = "https://railway.com/login"
    actions = [
        {"type": "wait", "ms": 10000},
        {"type": "evaluate", "script": "document.body.innerHTML"},
    ]
    
    print("Inspecting Railway login page...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        # The innerHTML will be in js_results[0]
        html = result.get("js_results", [{}])[0].get("result", "")
        with open("railway_login_dump.html", "w") as f:
            f.write(html)
        print("HTML dump saved.")
        with open("inspect_screenshot.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
    else:
        print(f"Failed: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(inspect_railway_login())

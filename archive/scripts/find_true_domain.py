
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def find_true_domain():
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
        {"type": "scroll", "direction": "down", "amount": 1000},
        {"type": "wait", "ms": 5000},
        {"type": "evaluate", "script": "document.body.innerText"},
    ]
    
    print("Finding the true public URL...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        text = result.get("js_results", [{}])[0].get("result", "")
        with open("true_domain_check.txt", "w") as f:
            f.write(text)
        with open("true_domain_screenshot.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
        print("Captured true domain info.")
    else:
        print(f"Failed: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(find_true_domain())

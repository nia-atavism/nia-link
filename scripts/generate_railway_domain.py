
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def generate_railway_domain():
    executor = ExecutorService(headless=False)
    
    url = "https://railway.com/dashboard"
    
    actions = [
        {"type": "wait", "ms": 5000},
        {"type": "click", "selector": "a:has-text('Nia-Link_v0.9')", "label": "Enter Project"},
        {"type": "wait", "ms": 3000},
        # 點擊服務方塊（假設只有一個服務）
        {"type": "click", "selector": "div[role='button']:has-text('Nia-Link')", "label": "Select Service"},
        {"type": "wait", "ms": 2000},
        {"type": "click", "selector": "button:has-text('Settings')", "label": "Settings"},
        {"type": "wait", "ms": 3000},
        {"type": "click", "selector": "button:has-text('Generate Domain')", "label": "Generate Domain"},
        {"type": "wait", "ms": 5000},
    ]
    
    print("Attempting to generate Railway domain...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        print("Domain generation sequence completed.")
        with open("railway_domain_gen.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
    else:
        print(f"Failed to generate domain: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(generate_railway_domain())

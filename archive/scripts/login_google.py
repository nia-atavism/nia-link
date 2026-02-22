
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def login_google():
    executor = ExecutorService(headless=True)
    
    url = "https://accounts.google.com/signin"
    actions = [
        {"type": "wait", "ms": 5000},
        {"type": "fill", "selector": "input[type='email']", "text": "linianrou1020@gmail.com"},
        {"type": "click", "selector": "#identifierNext"},
        {"type": "wait", "ms": 5000},
        {"type": "fill", "selector": "input[type='password']", "text": "dgfg03620362dgfg"},
        {"type": "click", "selector": "#passwordNext"},
        {"type": "wait", "ms": 10000},
    ]
    
    print("Logging into Google...")
    result = await executor.interact(url=url, actions=actions, account_id="google-nia")
    
    with open("google_login_result.png", "wb") as f:
        f.write(base64.b64decode(result["screenshot_base64"]))
    print("Saved screenshot.")

if __name__ == "__main__":
    asyncio.run(login_google())

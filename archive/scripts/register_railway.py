
import asyncio
import os
import sys
import base64
from pathlib import Path

# Add Nia-Link to path
sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")

from app.services.executor import ExecutorService

async def register_railway():
    # Railway registration usually requires GitHub login
    # We will try to go to railway.app/login and use GitHub
    # Note: Automation might be blocked by Cloudflare or GitHub anti-bot
    
    executor = ExecutorService(headless=False) # Use non-headless to see if we hit CAPTCHA
    
    url = "https://railway.com/login"
    actions = [
        {"type": "wait", "ms": 5000}, # Wait for Cloudflare
        {"type": "click", "selector": "button:has-text('GitHub')", "label": "GitHub Login"},
        {"type": "wait", "ms": 3000},
        # If redirected to GitHub login
        {"type": "fill", "selector": "#login_field", "text": "linianrou1020@gmail.com"},
        {"type": "fill", "selector": "#password", "text": "Nia@Atavism2026!"},
        {"type": "click", "selector": "input[type='submit']"},
        {"type": "wait", "ms": 10000}, # Wait for OAuth and redirection
    ]
    
    print(f"Starting registration for {url}...")
    result = await executor.interact(url=url, actions=actions, account_id="railway-nia")
    
    if result["status"] == "success":
        print("Success!")
        print(f"Screenshot saved to: {result['screenshot']}")
        if "viz_screenshot" in result:
             print(f"Visualization saved to: {result['viz_screenshot']}")
        # Save base64 for user to see
        with open("railway_reg_result.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
    else:
        print(f"Failed: {result.get('message')}")
        for entry in result.get("log", []):
            print(f"Log: {entry}")

if __name__ == "__main__":
    asyncio.run(register_railway())

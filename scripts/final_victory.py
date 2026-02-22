
import asyncio
import sys
import base64
import httpx
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def final_offensive(code):
    executor = ExecutorService(headless=True)
    session_id = "railway-final-victory"
    
    # 1. Login GitHub
    print("Step 1: Logging into GitHub...")
    await executor.interact(
        url="https://github.com/login",
        actions=[
            {"type": "wait", "ms": 5000},
            {"type": "fill", "selector": "#login_field", "text": "linianrou1020@gmail.com"},
            {"type": "fill", "selector": "#password", "text": "Nia@Atavism2026!"},
            {"type": "click", "selector": "input[type='submit']"},
            {"type": "wait", "ms": 5000},
        ],
        account_id=session_id
    )

    # 2. Enter 2FA Code
    print("Step 2: Entering 2FA Code...")
    res2 = await executor.interact(
        url="https://github.com/sessions/verified-device",
        actions=[
            {"type": "wait", "ms": 5000},
            {"type": "fill", "selector": "#otp", "text": code},
            {"type": "click", "selector": "button:has-text('Verify')"},
            {"type": "wait", "ms": 10000},
        ],
        account_id=session_id
    )
    with open("victory_step2.png", "wb") as f:
        f.write(base64.b64decode(res2["screenshot_base64"]))

    # 3. Railway Login & Authorize
    print("Step 3: Railway Login...")
    res3 = await executor.interact(
        url="https://railway.com/login",
        actions=[
            {"type": "wait", "ms": 10000},
            {"type": "click", "selector": "button:has-text('Continue with GitHub')"},
            {"type": "wait", "ms": 15000},
            # If Authorize exists
            {"type": "evaluate", "script": "const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')); if(b) b.click();"},
            {"type": "wait", "ms": 10000},
        ],
        account_id=session_id
    )

    # 4. Access Dashboard and check URL
    print("Step 4: Final Verification...")
    res4 = await executor.interact(
        url="https://railway.com/dashboard",
        actions=[
            {"type": "wait", "ms": 15000},
            {"type": "click", "selector": "a:has-text('Nia-Link_v0.9')"},
            {"type": "wait", "ms": 5000},
            {"type": "click", "selector": "div[role='button']:has-text('Nia-Link')"},
            {"type": "wait", "ms": 3000},
            {"type": "click", "selector": "button:has-text('Settings')"},
            {"type": "wait", "ms": 5000},
            {"type": "scroll", "direction": "down", "amount": 1200},
            {"type": "wait", "ms": 5000},
            {"type": "evaluate", "script": "document.body.innerText"}
        ],
        account_id=session_id
    )
    
    if res4["status"] == "success":
        with open("victory_final_check.png", "wb") as f:
            f.write(base64.b64decode(res4["screenshot_base64"]))
        text = res4.get("js_results", [{}])[0].get("result", "")
        with open("victory_dump.txt", "w") as f:
            f.write(text)
        print("VICTORY: Final data captured.")
    else:
        print(f"DEFEAT: {res4.get('message')}")

if __name__ == "__main__":
    asyncio.run(final_offensive(sys.argv[1]))

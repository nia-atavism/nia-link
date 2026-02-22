
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def the_real_victory(code):
    executor = ExecutorService(headless=True)
    session_id = f"final-victory-{int(asyncio.get_event_loop().time())}"
    
    # Step 1: GitHub Login
    print("1. GitHub Login...")
    await executor.interact(
        url="https://github.com/login",
        actions=[
            {"type": "fill", "selector": "#login_field", "text": "linianrou1020@gmail.com"},
            {"type": "fill", "selector": "#password", "text": "Nia@Atavism2026!"},
            {"type": "click", "selector": "input[type='submit']"},
            {"type": "wait", "ms": 5000},
        ],
        account_id=session_id
    )

    # Step 2: 2FA
    print("2. 2FA Code...")
    res2 = await executor.interact(
        url="https://github.com/sessions/verified-device",
        actions=[
            {"type": "fill", "selector": "#otp", "text": code},
            {"type": "click", "selector": "button:has-text('Verify')"},
            {"type": "wait", "ms": 8000},
        ],
        account_id=session_id
    )
    
    # Step 3: Railway Login
    print("3. Railway Auth...")
    # Use a direct JS click to be safe
    res3 = await executor.interact(
        url="https://railway.com/login",
        actions=[
            {"type": "wait", "ms": 10000},
            {"type": "evaluate", "script": "const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Continue with GitHub')); if(b) b.click();"},
            {"type": "wait", "ms": 15000},
            # Authorize if prompted
            {"type": "evaluate", "script": "const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')); if(b) b.click();"},
            {"type": "wait", "ms": 10000},
        ],
        account_id=session_id
    )
    with open("real_victory_step3.png", "wb") as f:
        f.write(base64.b64decode(res3["screenshot_base64"]))

    # Step 4: Harvest URL from Dashboard
    print("4. Dashboard URL Harvest...")
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
        with open("real_victory_final.png", "wb") as f:
            f.write(base64.b64decode(res4["screenshot_base64"]))
        text = res4.get("js_results", [{}])[0].get("result", "")
        with open("real_victory_dump.txt", "w") as f:
            f.write(text)
        print("REAL_VICTORY: Data captured.")
    else:
        print(f"FAILURE: {res4.get('message')}")

if __name__ == "__main__":
    asyncio.run(the_real_victory(sys.argv[1]))

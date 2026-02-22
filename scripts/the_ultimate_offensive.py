
import asyncio
import sys
import base64
import httpx
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def the_ultimate_offensive(code):
    executor = ExecutorService(headless=True)
    session_id = f"ultimate-victory-{int(asyncio.get_event_loop().time())}"
    
    # 全部動作合併在一個 URL 調用中
    url = "https://github.com/login"
    actions = [
        # 1. GitHub 登入
        {"type": "wait", "ms": 5000},
        {"type": "fill", "selector": "#login_field", "text": "linianrou1020@gmail.com"},
        {"type": "fill", "selector": "#password", "text": "Nia@Atavism2026!"},
        {"type": "click", "selector": "input[type='submit']"},
        {"type": "wait", "ms": 5000},
        
        # 2. 輸入 2FA Code (如果頁面不對就跳過)
        {"type": "evaluate", "script": f"""
            const otpInput = document.querySelector('#otp');
            if (otpInput) {{
                otpInput.value = '{code}';
                const verifyBtn = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Verify'));
                if (verifyBtn) verifyBtn.click();
            }}
        """},
        {"type": "wait", "ms": 10000},
        
        # 3. 跳轉至 Railway Login
        {"type": "evaluate", "script": "window.location.href = 'https://railway.com/login'"},
        {"type": "wait", "ms": 10000},
        
        # 4. 點擊 Railway 的 GitHub 登入
        {"type": "evaluate", "script": "const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Continue with GitHub')); if(b) b.click();"},
        {"type": "wait", "ms": 15000},
        
        # 5. 如果出現 Authorize 頁面
        {"type": "evaluate", "script": "const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')); if(b) b.click();"},
        {"type": "wait", "ms": 15000},
        
        # 6. 最後進入 Dashboard 確認網址
        {"type": "evaluate", "script": "window.location.href = 'https://railway.com/dashboard'"},
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
    ]
    
    print("Starting Ultimate Offensive...")
    result = await executor.interact(url=url, actions=actions, account_id=session_id)
    
    if result["status"] == "success":
        with open("ultimate_victory_final.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
        text = result.get("js_results", [{}])[-1].get("result", "")
        with open("ultimate_victory_dump.txt", "w") as f:
            f.write(text)
        print("ULTIMATE_VICTORY: Data captured.")
        
        # 嘗試從 dump 中找網址
        import re
        match = re.search(r'https://[a-zA-Z0-9-]+\.up\.railway\.app', text)
        if match:
            print(f"FOUND_URL: {match.group(0)}")
    else:
        print(f"FAILED: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(the_ultimate_offensive(sys.argv[1]))

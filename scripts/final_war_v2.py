
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def final_war_v2(code):
    executor = ExecutorService(headless=True)
    session_id = f"victory-v2-{int(asyncio.get_event_loop().time())}"
    
    # 全部動作合併在一個 URL 調用中，改用座標點擊避開影子 DOM
    url = "https://github.com/login"
    actions = [
        # 1. GitHub 登入
        {"type": "fill", "selector": "#login_field", "text": "linianrou1020@gmail.com"},
        {"type": "fill", "selector": "#password", "text": "Nia@Atavism2026!"},
        {"type": "click", "selector": "input[type='submit']"},
        {"type": "wait", "ms": 5000},
        
        # 2. 2FA (在 JS 中執行)
        {"type": "evaluate", "script": f"""
            const otp = document.querySelector('#otp');
            if (otp) {{
                otp.value = '{code}';
                const btn = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Verify'));
                if (btn) btn.click();
            }}
        """},
        {"type": "wait", "ms": 10000},
        
        # 3. 進入 Railway
        {"type": "evaluate", "script": "window.location.href = 'https://railway.com/login'"},
        {"type": "wait", "ms": 10000},
        
        # 4. 暴力座標點擊 (中心位置通常是 GitHub 按鈕)
        {"type": "evaluate", "script": "window.scrollTo(0, 0);"},
        {"type": "wait", "ms": 2000},
        # 模擬點擊中心偏下區域 (1280x720 的中心是 640, 360)
        {"type": "evaluate", "script": "document.elementFromPoint(640, 480).click();"},
        {"type": "wait", "ms": 15000},
        
        # 5. 最後確認 Dashboard
        {"type": "evaluate", "script": "window.location.href = 'https://railway.com/dashboard'"},
        {"type": "wait", "ms": 10000},
        {"type": "evaluate", "script": "document.body.innerText"}
    ]
    
    print("Launching Final Offensive V2...")
    result = await executor.interact(url=url, actions=actions, account_id=session_id)
    
    if result["status"] == "success":
        with open("v2_victory_check.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
        print("V2 offensive finished.")
    else:
        print(f"FAILED: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(final_war_v2(sys.argv[1]))

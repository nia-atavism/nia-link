
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def final_war_v3(code):
    executor = ExecutorService(headless=True)
    session_id = f"victory-v3-{int(asyncio.get_event_loop().time())}"
    
    # 增加 timeout 避免字體載入導致的截圖失敗
    url = "https://github.com/login"
    actions = [
        # 1. GitHub 登入
        {"type": "fill", "selector": "#login_field", "text": "linianrou1020@gmail.com"},
        {"type": "fill", "selector": "#password", "text": "Nia@Atavism2026!"},
        {"type": "click", "selector": "input[type='submit']"},
        {"type": "wait", "ms": 5000},
        
        # 2. 2FA (在 JS 中執行)
        {"type": "evaluate", "script": f"const otp = document.querySelector('#otp'); if (otp) {{ otp.value = '{code}'; document.querySelector('button[type=submit]').click(); }}"},
        {"type": "wait", "ms": 10000},
        
        # 3. 進入 Railway
        {"type": "evaluate", "script": "window.location.href = 'https://railway.com/login'"},
        {"type": "wait", "ms": 10000},
        
        # 4. 暴力點擊 GitHub 按鈕 (使用更精準的 JS)
        {"type": "evaluate", "script": """
            const githubBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('GitHub'));
            if (githubBtn) githubBtn.click();
        """},
        {"type": "wait", "ms": 15000},
        
        # 5. Dashboard 確認 (不使用截圖，改用 innerText)
        {"type": "evaluate", "script": "window.location.href = 'https://railway.com/dashboard'"},
        {"type": "wait", "ms": 10000},
        {"type": "evaluate", "script": "document.body.innerText"}
    ]
    
    print("Launching Final Offensive V3...")
    # 這裡我們不使用 executor.interact，因為它最後強制截圖
    # 我們改寫一個不截圖的版本
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url)
            for action in actions:
                if action["type"] == "fill":
                    await page.fill(action["selector"], action["text"])
                elif action["type"] == "click":
                    await page.click(action["selector"])
                elif action["type"] == "wait":
                    await page.wait_for_timeout(action["ms"])
                elif action["type"] == "evaluate":
                    res = await page.evaluate(action["script"])
                    if action.get("script") == "document.body.innerText":
                        with open("v3_victory_dump.txt", "w") as f:
                            f.write(res)
            
            # 手動截圖 (不等待字體)
            await page.screenshot(path="v3_victory_check.png", timeout=5000)
            print("V3 offensive finished.")
        except Exception as e:
            print(f"FAILED: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(final_war_v3(sys.argv[1]))

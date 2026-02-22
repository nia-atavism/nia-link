
import asyncio
import sys
import base64
from pathlib import Path

sys.path.append("/Users/nia/Documents/Nia-Link_v0.9")
from app.services.executor import ExecutorService

async def debug_railway_click(code):
    executor = ExecutorService(headless=True)
    session_id = f"debug-click-{int(asyncio.get_event_loop().time())}"
    
    url = "https://railway.com/login"
    actions = [
        {"type": "wait", "ms": 10000},
        # 1. 紀錄點擊前的狀態
        {"type": "evaluate", "script": "document.body.innerHTML"},
        # 2. 嘗試多種方式點擊 GitHub 按鈕
        {"type": "evaluate", "script": """
            console.log("Attempting clicks...");
            const buttons = Array.from(document.querySelectorAll('button'));
            const githubBtn = buttons.find(b => b.innerText.includes('Continue with GitHub') || b.innerHTML.includes('github'));
            if (githubBtn) {
                const rect = githubBtn.getBoundingClientRect();
                console.log("Button found at:", rect.x, rect.y);
                githubBtn.click();
                return "Clicked via JS";
            }
            return "Button not found in JS";
        """},
        {"type": "wait", "ms": 10000},
        # 3. 紀錄點擊後的狀態
        {"type": "evaluate", "script": "window.location.href"},
    ]
    
    print("Debugging Railway Login Click...")
    result = await executor.interact(url=url, actions=actions, account_id=session_id)
    
    if result["status"] == "success":
        with open("debug_click_final.png", "wb") as f:
            f.write(base64.b64decode(result["screenshot_base64"]))
        print("Debug info captured.")
        for i, res in enumerate(result.get("js_results", [])):
            print(f"JS Result {i}: {res.get('result')[:500] if isinstance(res.get('result'), str) else res.get('result')}")
    else:
        print(f"FAILED: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(debug_railway_click(sys.argv[1]))

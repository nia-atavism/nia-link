
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def the_persistent_offensive(code):
    async with async_playwright() as p:
        # 增加導航超時時間
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_user_data_persistent",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(60000) # 60s
        
        try:
            # 1. 登入 GitHub
            print("1. GitHub Login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            
            # 2. 處理 2FA
            if "verified-device" in page.url:
                print("2. 2FA Input...")
                await page.fill("#otp", code)
                await page.click("button[type='submit']")
                await page.wait_for_timeout(5000)
            
            # 3. 登入 Railway
            print("3. Railway Login...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(15000)
            
            # 點擊 GitHub 按鈕
            print("Clicking GitHub Button...")
            await page.evaluate("""
                const btns = Array.from(document.querySelectorAll('button'));
                const target = btns.find(b => b.innerText.includes('GitHub'));
                if (target) target.click();
            """)
            
            # 4. 關鍵循環：等待授權或 Dashboard
            print("4. Waiting for redirect...")
            for _ in range(6): # 最多等待 60s
                print(f"Current URL: {page.url}")
                if "dashboard" in page.url:
                    break
                if "github.com/login/oauth" in page.url:
                    print("Authorizing...")
                    await page.evaluate("""
                        const btns = Array.from(document.querySelectorAll('button'));
                        const target = btns.find(b => b.innerText.includes('Authorize'));
                        if (target) target.click();
                    """)
                await page.wait_for_timeout(10000)
            
            # 5. 最後巡檢
            if "dashboard" in page.url:
                print("5. Project Details...")
                await page.goto("https://railway.com/dashboard")
                await page.wait_for_timeout(15000)
                
                # 點擊專案進入詳情（這裡的路徑可能需要微調）
                try:
                    await page.click("a:has-text('Nia-Link_v0.9')")
                    await page.wait_for_timeout(5000)
                    await page.click("button:has-text('Settings')")
                    await page.wait_for_timeout(5000)
                    await page.evaluate("window.scrollTo(0, 1000)")
                    await page.wait_for_timeout(2000)
                    
                    content = await page.evaluate("document.body.innerText")
                    with open("persistent_victory_dump.txt", "w") as f:
                        f.write(content)
                    await page.screenshot(path="persistent_victory_final.png")
                    print("PERSISTENT_VICTORY: Mission Accomplished.")
                except Exception as e:
                    await page.screenshot(path="persistent_part_fail.png")
                    print(f"Partial Fail at Project detail: {e}")
            else:
                await page.screenshot(path="persistent_fail.png")
                print(f"FAILED: Stuck at {page.url}")
                
        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(the_persistent_offensive(sys.argv[1]))

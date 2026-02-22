
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def the_atomic_offensive(code):
    async with async_playwright() as p:
        # 使用持久化上下文以保持 Session
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_user_data",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        
        try:
            # 1. 登入 GitHub
            print("1. GitHub Login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            
            # 2. 處理 2FA
            print("2. 2FA Check...")
            if "verified-device" in page.url:
                await page.fill("#otp", code)
                await page.click("button[type='submit']")
                await page.wait_for_timeout(5000)
            
            # 3. 進入 Railway 並點擊登入
            print("3. Railway Login...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            # 使用更暴力的方式尋找按鈕
            await page.evaluate("""
                const btns = Array.from(document.querySelectorAll('button'));
                const target = btns.find(b => b.innerText.includes('GitHub'));
                if (target) target.click();
            """)
            await page.wait_for_timeout(15000)
            
            # 4. 處理 GitHub 授權頁面 (如果出現)
            if "github.com/login/oauth" in page.url:
                print("4. Authorizing Railway on GitHub...")
                await page.evaluate("""
                    const btns = Array.from(document.querySelectorAll('button'));
                    const target = btns.find(b => b.innerText.includes('Authorize'));
                    if (target) target.click();
                """)
                await page.wait_for_timeout(10000)
            
            # 5. 進入 Dashboard 並抓取網址
            print("5. Project Inspection...")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(15000)
            
            # 如果成功進入 Dashboard，點擊專案
            if "dashboard" in page.url:
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(5000)
                await page.click("div[role='button']:has-text('Nia-Link')")
                await page.wait_for_timeout(3000)
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(5000)
                await page.evaluate("window.scrollTo(0, 1000)")
                await page.wait_for_timeout(2000)
                
                # 抓取最終資訊
                content = await page.evaluate("document.body.innerText")
                with open("atomic_victory_dump.txt", "w") as f:
                    f.write(content)
                await page.screenshot(path="atomic_victory_final.png")
                print("ATOMIC_VICTORY: Mission Accomplished.")
            else:
                await page.screenshot(path="atomic_fail.png")
                print(f"FAILED: Current URL is {page.url}")
                
        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(the_atomic_offensive(sys.argv[1]))

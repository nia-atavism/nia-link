
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def last_hope(code):
    async with async_playwright() as p:
        # 使用持久化上下文以確保所有步驟在同一 Session 下完成
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_last_hope",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(120000)
        
        try:
            # 1. 登入 GitHub
            print("1. GitHub Auth...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            
            # 2. 處理 2FA
            if "verified-device" in page.url:
                print(f"2. 2FA: {code}")
                await page.fill("#otp", code)
                await page.click("button[type='submit']")
                await page.wait_for_load_state("networkidle")
            
            # 3. 進入 Railway 並點擊
            print("3. Railway Login...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(15000)
            
            # 使用更精確的 Selector 並等待按鈕可見
            print("Locating GitHub button...")
            github_btn = page.locator("button:has-text('Continue with GitHub')")
            await github_btn.wait_for(state="visible")
            await github_btn.click()
            print("Clicked GitHub Button.")
            
            # 4. 關鍵：等待授權或跳轉
            print("4. Redirect handling...")
            for i in range(12): # 最多等待 120s
                print(f"Step {i}, URL: {page.url}")
                if "dashboard" in page.url:
                    break
                if "github.com/login/oauth" in page.url:
                    print("Authorizing Railway...")
                    auth_btn = page.locator("button:has-text('Authorize')")
                    if await auth_btn.is_visible():
                        await auth_btn.click()
                await page.wait_for_timeout(10000)
            
            # 5. 抓取最終資訊
            if "dashboard" in page.url:
                print("5. Inspection...")
                await page.goto("https://railway.com/dashboard")
                await page.wait_for_timeout(15000)
                
                # 點擊專案
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(10000)
                
                # 抓取網址
                text = await page.evaluate("document.body.innerText")
                with open("last_hope_dump.txt", "w") as f:
                    f.write(text)
                await page.screenshot(path="last_hope_final.png")
                print("LAST_HOPE_SUCCESS.")
            else:
                await page.screenshot(path="last_hope_fail.png")
                print(f"STUCK_AT: {page.url}")

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
            await page.screenshot(path="last_hope_error.png")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(last_hope(sys.argv[1]))

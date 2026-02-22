
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def the_guaranteed_victory(code):
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_guaranteed_victory",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(120000)
        
        try:
            # 1. GitHub 登入 + 2FA
            print("1. GitHub login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            if "verified-device" in page.url:
                print(f"Entering 2FA: {code}")
                await page.fill("#otp", code)
                await page.click("button[type='submit']")
                await page.wait_for_load_state("networkidle")

            # 2. 進入 Railway 登入頁面
            print("2. Railway login portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            
            # 點擊 GitHub 按鈕
            print("Clicking GitHub Button...")
            await page.evaluate("Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('GitHub')).click();")
            await page.wait_for_timeout(15000)

            # 3. 處理 GitHub 的「確認重定向」或「重新輸入密碼」
            print(f"Current URL: {page.url}")
            if "github.com/login" in page.url:
                print("Re-authenticating GitHub session...")
                await page.fill("#password", "Nia@Atavism2026!")
                await page.click("input[type='submit']")
                await page.wait_for_timeout(15000)

            # 4. 處理 Authorize
            if "oauth/authorize" in page.url:
                print("Granting Authorization...")
                await page.evaluate("Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click();")
                await page.wait_for_timeout(15000)

            # 5. 確保進入 Dashboard
            print(f"Dashboard check at: {page.url}")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(15000)
            
            # 保存證據
            await page.screenshot(path="guaranteed_victory_final.png")
            text = await page.evaluate("document.body.innerText")
            with open("guaranteed_victory_dump.txt", "w") as f:
                f.write(text)

            if "Nia-Link" in text:
                print("GUARANTEED_VICTORY: SUCCESS.")
                # 獲取 URL
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(8000)
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(8000)
                final_url = await page.evaluate("Array.from(document.querySelectorAll('a')).find(l => l.href.includes('.up.railway.app')).href")
                print(f"FINAL_URL: {final_url}")
            else:
                print("FAILED: PROJECT NOT FOUND.")

        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(the_guaranteed_victory(sys.argv[1]))


import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def victory_strike(code):
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_victory_strike",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(120000)
        
        try:
            # 1. 確保 GitHub 登入且 2FA 通過
            print("1. Logging into GitHub...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            
            if "verified-device" in page.url:
                print(f"Entering 2FA Code: {code}")
                await page.fill("#otp", code)
                await page.click("button[type='submit']")
                await page.wait_for_load_state("networkidle")
            
            print(f"GitHub Status: {page.url}")

            # 2. 進入 Railway 並處理跳轉
            print("2. Railway Auth Link...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(15000)
            
            # 點擊 GitHub 按鈕
            await page.evaluate("Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('GitHub')).click();")
            await page.wait_for_timeout(15000)

            # 3. 強制處理可能出現的 GitHub 登入確認（這是之前的卡點！）
            if "github.com/login" in page.url and "client_id" in page.url:
                print("Found secondary GitHub login prompt. Re-filling password...")
                # 這裡 GitHub 有時會要求重新輸入密碼以確認身份
                pwd_field = page.locator("#password")
                if await pwd_field.is_visible():
                    await page.fill("#password", "Nia@Atavism2026!")
                    await page.click("input[type='submit']")
                    await page.wait_for_timeout(15000)

            # 4. 處理授權
            if "github.com/login/oauth/authorize" in page.url:
                print("Clicking final Authorize button...")
                await page.evaluate("Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click();")
                await page.wait_for_timeout(20000)

            # 5. 最後 Dashboard 驗證
            print("5. Inspection...")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(20000)
            
            text = await page.evaluate("document.body.innerText")
            with open("victory_strike_dump.txt", "w") as f:
                f.write(text)
            await page.screenshot(path="victory_strike_final.png")
            
            if "Nia-Link" in text:
                print("VICTORY_STRIKE: SUCCESS.")
            else:
                print(f"FAILED: Current URL {page.url}")

        except Exception as e:
            print(f"ERROR: {e}")
            await page.screenshot(path="victory_strike_error.png")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(victory_strike(sys.argv[1]))

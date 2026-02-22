
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def the_ironclad_offensive(code):
    async with async_playwright() as p:
        # 增加啟動參數避免被偵測
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(120000)
        
        try:
            # 1. GitHub Login
            print("1. GitHub login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            
            # 2. 處理 2FA (使用更靈活的 Selector)
            print("2. 2FA Check...")
            await page.wait_for_timeout(5000)
            if "verified-device" in page.url:
                print("Entering code...")
                otp_field = page.locator("input[name='otp']")
                if await otp_field.is_hidden(): # 某些情況下 ID 是 otp
                    otp_field = page.locator("#otp")
                await otp_field.fill(code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            # 3. 進入 Railway 並登入
            print("3. Railway portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            
            # 使用座標點擊 (強制命中)
            print("Force clicking login button area...")
            await page.mouse.click(640, 480) 
            await page.wait_for_timeout(20000)

            # 4. 授權處理
            if "github.com" in page.url and "authorize" in page.url:
                print("4. Authorizing...")
                auth_btn = page.locator("button:has-text('Authorize')")
                if await auth_btn.is_visible():
                    await auth_btn.click()
                    await page.wait_for_timeout(15000)

            # 5. 巡航 Dashboard
            print("5. Inspection...")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(10000)
            
            # 保存結果
            await page.screenshot(path="ironclad_victory_final.png")
            text = await page.evaluate("document.body.innerText")
            with open("ironclad_victory_dump.txt", "w") as f:
                f.write(text)

            if "Nia-Link" in text:
                print("IRONCLAD_SUCCESS.")
                # 提取 URL
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(8000)
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(8000)
                final_url = await page.evaluate("Array.from(document.querySelectorAll('a')).find(l => l.href.includes('.up.railway.app')).href")
                print(f"URL: {final_url}")
            else:
                print(f"FAILED. Currently at: {page.url}")

        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(the_ironclad_offensive(sys.argv[1]))

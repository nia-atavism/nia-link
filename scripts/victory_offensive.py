
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def victory_offensive(code):
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_victory_offensive",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(90000)
        
        try:
            # 1. GitHub 登入
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
                # 使用 click 並等待特定元素出現，而不是 evaluate
                async with page.expect_navigation():
                    await page.click("button[type='submit']")
                print("2FA Success.")

            # 3. 進入 Railway 並點擊登入
            print("3. Railway Login...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            
            # 使用座標點擊避開影子 DOM 難題
            print("Clicking GitHub button via coordinate (640, 480)...")
            await page.mouse.click(640, 480)
            await page.wait_for_timeout(20000)

            # 4. 如果出現 Authorize 頁面
            if "github.com/login/oauth" in page.url:
                print("4. Authorizing...")
                # 授權按鈕通常在頁面較下方，點擊中心位置或尋找按鈕
                await page.evaluate("Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click();")
                await page.wait_for_timeout(15000)

            # 5. 最後 Dashboard 驗證
            print("5. Inspection...")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(15000)
            
            text = await page.evaluate("document.body.innerText")
            with open("victory_offensive_dump.txt", "w") as f:
                f.write(text)
            await page.screenshot(path="victory_offensive_final.png")
            
            if "Nia-Link" in text:
                print("VICTORY_OFFENSIVE: Success.")
            else:
                print(f"STUCK_AT: {page.url}")

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(victory_offensive(sys.argv[1]))

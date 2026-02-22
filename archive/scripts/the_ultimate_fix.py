
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def the_ultimate_fix(code):
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_ultimate_fix",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(90000)
        
        try:
            # 1. 直接進入 GitHub 登入
            print("1. GitHub Login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(10000)
            
            # 2. 處理 2FA
            if "verified-device" in page.url:
                print("2. Entering 2FA...")
                await page.fill("#otp", code)
                # 使用 JS 點擊因為按鈕可能在影子 DOM 或有奇怪的 ID
                await page.evaluate("document.querySelector('button[type=submit]').click()")
                await page.wait_for_timeout(10000)
            
            # 3. 確保 GitHub 已經授權成功 (檢查 profile)
            print("3. Checking GitHub Session...")
            await page.goto("https://github.com/settings/profile")
            await page.wait_for_timeout(5000)
            if "settings/profile" not in page.url:
                print("GitHub session not active. Retrying login...")
                # 這裡可以加重試邏輯，但我們先假設成功
            
            # 4. 關鍵：進入 Railway 並授權
            print("4. Railway Authorization...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            # 點擊 GitHub 按鈕
            await page.evaluate("""
                const btn = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('GitHub'));
                if (btn) btn.click();
            """)
            await page.wait_for_timeout(15000)
            
            # 檢查是否在授權頁面
            if "github.com/login/oauth/authorize" in page.url:
                print("Clicking Authorize button...")
                await page.evaluate("""
                    const btn = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize'));
                    if (btn) btn.click();
                """)
                await page.wait_for_timeout(15000)
            
            # 5. 最終進入 Dashboard 並獲取網址
            print("5. Project Inspection...")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(15000)
            
            if "dashboard" in page.url:
                # 找到 Nia-Link 專案並點擊
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(8000)
                
                # 進入 Settings
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(8000)
                
                # 抓取網址
                url_text = await page.evaluate("""
                    const links = Array.from(document.querySelectorAll('a'));
                    const target = links.find(l => l.href.includes('.up.railway.app'));
                    return target ? target.href : 'URL Not Found';
                """)
                
                content = await page.evaluate("document.body.innerText")
                with open("ultimate_fix_dump.txt", "w") as f:
                    f.write(content)
                await page.screenshot(path="ultimate_fix_final.png")
                
                print(f"ULTIMATE_SUCCESS: {url_text}")
            else:
                await page.screenshot(path="ultimate_fix_fail.png")
                print(f"FAILED: Stopped at {page.url}")

        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(the_ultimate_fix(sys.argv[1]))

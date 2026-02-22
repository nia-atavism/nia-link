
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def the_stable_victory(code):
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_stable_victory",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(90000)
        
        try:
            # Step 1: GitHub Login
            print("1. GitHub Login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            
            # Step 2: 2FA with retry-resistant logic
            print("2. 2FA Check...")
            await page.wait_for_timeout(5000)
            if "verified-device" in page.url:
                print("2FA required. Entering code...")
                await page.fill("#otp", code)
                # 使用 click 替代 evaluate 以免 navigation 導致錯誤
                await page.click("button[type='submit']")
                await page.wait_for_load_state("networkidle")
            
            # Step 3: Railway Login
            print("3. Railway Auth...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            # 使用 JS 點擊但加上 try-catch
            await page.evaluate("""
                try {
                    const btn = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('GitHub'));
                    if (btn) btn.click();
                } catch(e) {}
            """)
            
            # Step 4: OAuth Authorization
            print("4. Waiting for OAuth...")
            for _ in range(10): # 100s
                print(f"URL: {page.url}")
                if "dashboard" in page.url: break
                if "github.com/login/oauth/authorize" in page.url:
                    print("Clicking Authorize...")
                    await page.evaluate("try { Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click(); } catch(e) {}")
                await page.wait_for_timeout(10000)
            
            # Step 5: Dashboard Extraction
            if "dashboard" in page.url:
                print("5. Extracting Data...")
                await page.goto("https://railway.com/dashboard")
                await page.wait_for_timeout(15000)
                
                # 進入專案詳情
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(10000)
                
                # 進入 Settings 獲取網址
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(8000)
                
                url_final = await page.evaluate("""
                    Array.from(document.querySelectorAll('a'))
                    .find(l => l.href.includes('.up.railway.app')).href
                """)
                
                await page.screenshot(path="stable_victory_final.png")
                print(f"STABLE_SUCCESS: {url_final}")
            else:
                await page.screenshot(path="stable_victory_fail.png")
                print(f"STABLE_FAIL: Stuck at {page.url}")

        except Exception as e:
            print(f"CRITICAL_FAIL: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(the_stable_victory(sys.argv[1]))

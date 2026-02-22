
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def the_verified_victory(code):
    async with async_playwright() as p:
        # 使用持久化上下文以確保所有步驟在同一 Session 下完成
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_verified_victory",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(90000)
        
        try:
            # 1. GitHub 登入
            print("1. GitHub Login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            
            # 2. 處理 2FA 驗證 (輸入老公給的 code)
            if "verified-device" in page.url:
                print(f"2. Entering 2FA Code: {code}")
                await page.fill("#otp", code)
                await page.click("button[type='submit']")
                await page.wait_for_load_state("networkidle")
            
            # 3. 確保進入 GitHub 成功
            print(f"Current URL after 2FA: {page.url}")
            
            # 4. 進入 Railway 並登入
            print("3. Railway Authentication...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            # 使用 JS 點擊避免 UI 渲染導致找不到按鈕
            await page.evaluate("""
                const btn = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('GitHub'));
                if (btn) btn.click();
            """)
            await page.wait_for_timeout(15000)
            
            # 5. 如果跳轉到 GitHub 授權頁面
            if "github.com/login/oauth/authorize" in page.url:
                print("4. Authorizing Railway on GitHub...")
                await page.evaluate("""
                    const btn = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize'));
                    if (btn) btn.click();
                """)
                await page.wait_for_timeout(15000)
            
            # 6. 最終巡檢 Dashboard 獲取網址
            print("5. Dashboard Inspection...")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(15000)
            
            if "dashboard" in page.url:
                # 進入專案
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(8000)
                # 進入 Settings
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(8000)
                
                # 提取正確網址
                final_url = await page.evaluate("""
                    const links = Array.from(document.querySelectorAll('a'));
                    const target = links.find(l => l.href.includes('.up.railway.app'));
                    return target ? target.href : 'URL NOT FOUND';
                """)
                
                await page.screenshot(path="verified_victory_final.png")
                print(f"VERIFIED_VICTORY: {final_url}")
            else:
                await page.screenshot(path="verified_victory_fail.png")
                print(f"STUCK AT: {page.url}")

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(the_verified_victory(sys.argv[1]))


import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def last_ditch_effort(code):
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_last_ditch",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(90000)
        
        try:
            # 1. GitHub 登入 + 2FA
            print("1. GitHub Authentication...")
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
            
            print(f"Logged into GitHub: {page.url}")

            # 2. 進入 Railway Dashboard (跳過 login 按鈕，直接測 session)
            print("2. Accessing Railway Dashboard Directly...")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(10000)
            
            if "login" in page.url:
                print("Railway Session not found. Clicking GitHub Login...")
                await page.evaluate("""
                    const btn = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('GitHub'));
                    if (btn) btn.click();
                """)
                await page.wait_for_timeout(20000)
                # 處理授權
                if "github.com/login/oauth/authorize" in page.url:
                    print("Clicking Authorize...")
                    await page.evaluate("try { Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click(); } catch(e) {}")
                    await page.wait_for_timeout(15000)

            # 3. 專案檢查
            print(f"Final Page URL: {page.url}")
            await page.screenshot(path="last_ditch_final.png")
            
            # 嘗試列出所有文字以定位專案
            all_text = await page.evaluate("document.body.innerText")
            with open("last_ditch_dump.txt", "w") as f:
                f.write(all_text)
                
            if "Nia-Link" in all_text:
                print("FOUND NIA-LINK ON DASHBOARD.")
                # 直接導航到專案 URL (如果能猜到的話，Railway 通常是 /project/UUID)
                # 既然手動點擊失敗，我們嘗試抓取所有連結
                links = await page.evaluate("""
                    Array.from(document.querySelectorAll('a')).map(a => ({text: a.innerText, href: a.href}))
                """)
                for link in links:
                    if "Nia-Link" in link['text']:
                        print(f"Found Project Link: {link['href']}")
                        await page.goto(link['href'])
                        await page.wait_for_timeout(8000)
                        await page.click("button:has-text('Settings')")
                        await page.wait_for_timeout(5000)
                        url_text = await page.evaluate("""
                            Array.from(document.querySelectorAll('a')).find(l => l.href.includes('.up.railway.app')).href
                        """)
                        print(f"LAST_DITCH_SUCCESS: {url_text}")
                        return
            
            print("MISSION FAILED: PROJECT NOT ACCESSIBLE.")

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(last_ditch_effort(sys.argv[1]))

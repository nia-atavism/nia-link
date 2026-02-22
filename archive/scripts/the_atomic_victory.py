
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def the_atomic_victory(code):
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_atomic_victory",
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
            
            # 2. 處理 2FA
            if "verified-device" in page.url:
                print(f"2. Entering 2FA: {code}")
                await page.fill("#otp", code)
                # 使用暴力點擊，不等待 navigation
                await page.evaluate("document.querySelector('button[type=submit]').click();")
                print("Clicked Verify. Waiting 15s...")
                await page.wait_for_timeout(15000)

            # 3. 強行進入 Railway Login 頁面並點擊 GitHub 按鈕
            print(f"3. Entering Railway Login (Current: {page.url})")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            
            print("Clicking GitHub Button via atomic JS...")
            # 暴力尋找所有可能包含 GitHub 的按鈕並點擊
            await page.evaluate("""
                const btns = Array.from(document.querySelectorAll('button'));
                const target = btns.find(b => b.innerText.includes('GitHub') || b.innerHTML.includes('github'));
                if (target) {
                    target.click();
                } else {
                    // 如果按鈕在影子 DOM 裡，嘗試點擊中心位置
                    document.elementFromPoint(640, 480).click();
                }
            """)
            print("Button clicked. Waiting for OAuth redirect (20s)...")
            await page.wait_for_timeout(20000)

            # 4. 處理可能的 GitHub 授權按鈕
            if "github.com/login/oauth" in page.url:
                print("4. Authorizing Railway...")
                await page.evaluate("""
                    const btns = Array.from(document.querySelectorAll('button'));
                    const target = btns.find(b => b.innerText.includes('Authorize'));
                    if (target) target.click();
                """)
                await page.wait_for_timeout(10000)

            # 5. 最終嘗試獲取 Dashboard 內容
            print(f"5. Final check at {page.url}...")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(15000)
            
            all_text = await page.evaluate("document.body.innerText")
            with open("atomic_dump.txt", "w") as f:
                f.write(all_text)
            await page.screenshot(path="atomic_final.png")
            
            if "Nia-Link" in all_text:
                print("ATOMIC_VICTORY: Project found.")
            else:
                print("ATOMIC_FAILURE: Dashboard not accessible.")

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(the_atomic_victory(sys.argv[1]))

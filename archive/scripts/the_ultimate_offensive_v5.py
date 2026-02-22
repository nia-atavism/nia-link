
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def the_ultimate_offensive_v5(code):
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_v5_data",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(90000)
        
        try:
            # 1. GitHub Login
            print("1. GitHub Login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            
            if "verified-device" in page.url:
                print(f"2. 2FA Input: {code}")
                await page.fill("#otp", code)
                # 使用簡單點擊，不引發 context 銷毀
                await page.click("button[type='submit']")
                await page.wait_for_timeout(10000)

            print(f"Current URL: {page.url}")

            # 3. 進入 Railway 並點擊
            print("3. Railway Login Step...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            
            # 使用 JS 直接找到按鈕並派發事件，比直接點擊更可靠
            print("Invoking GitHub button via advanced JS...")
            await page.evaluate("""
                const btn = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('GitHub'));
                if (btn) {
                    const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
                    btn.dispatchEvent(clickEvent);
                } else {
                    // 備案：如果找不到按鈕，可能是因為還在加載，強制點擊座標
                    const el = document.elementFromPoint(640, 480);
                    if (el) el.click();
                }
            """)
            await page.wait_for_timeout(15000)

            # 4. 授權
            if "github.com/login/oauth" in page.url:
                print("4. Final Authorization...")
                await page.evaluate("""
                    const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize'));
                    if (b) b.click();
                """)
                await page.wait_for_timeout(10000)

            # 5. 確認
            print("5. Inspecting Dashboard...")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(15000)
            
            all_text = await page.evaluate("document.body.innerText")
            with open("v5_final_dump.txt", "w") as f:
                f.write(all_text)
            await page.screenshot(path="v5_final_check.png")
            
            if "Nia-Link" in all_text:
                print("SUCCESS: V5 Accomplished.")
                # 獲取具體網址
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(5000)
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(5000)
                url_final = await page.evaluate("Array.from(document.querySelectorAll('a')).find(l => l.href.includes('.up.railway.app')).href")
                print(f"FINAL_URL: {url_final}")
            else:
                print(f"STILL_STUCK: {page.url}")

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(the_ultimate_offensive_v5(sys.argv[1]))

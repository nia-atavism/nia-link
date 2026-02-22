
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def run(code):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_timeout(90000)

        try:
            # 1. GitHub Login + 2FA
            print("1. GitHub login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            if "verified-device" in page.url:
                print(f"2. 2FA Input: {code}")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")

            # 2. Railway Portal
            print("3. Railway login...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            
            # Click GitHub - using coordinate to be safe
            await page.mouse.click(640, 480)
            await page.wait_for_timeout(20000)
            
            # Authorization loop
            for _ in range(5):
                if "dashboard" in page.url: break
                if "login" in page.url and "github" in page.url:
                    await page.fill("#password", "Nia@Atavism2026!")
                    await page.click("input[type='submit']")
                if "authorize" in page.url:
                    await page.evaluate("try { Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click(); } catch(e) {}")
                await page.wait_for_timeout(10000)

            # 3. If Dashboard, enter and get URL
            if "dashboard" in page.url:
                print("4. Inspecting Dashboard...")
                # Find Nia-Link
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(10000)
                
                # Check for active domain in settings
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(10000)
                await page.evaluate("window.scrollTo(0, 1000)")
                
                # Get the link
                url = await page.evaluate("""
                    Array.from(document.querySelectorAll('a'))
                    .find(l => l.href.includes('.up.railway.app')).href
                """)
                print(f"VICTORY_URL: {url}")
                await page.screenshot(path="victory_check.png")
            else:
                print(f"STUCK_AT: {page.url}")
                await page.screenshot(path="victory_fail.png")

        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

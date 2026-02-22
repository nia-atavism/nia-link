
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def run(code):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a consistent user data dir to maintain state across attempts in this script
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_timeout(60000)

        async def github_login():
            print("Action: GitHub Login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            if "verified-device" in page.url:
                print(f"Action: Entering 2FA {code}...")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")

        async def railway_auth():
            print("Action: Railway Login...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            print("Action: Clicking GitHub Button...")
            # Click the button precisely
            await page.mouse.click(640, 480)
            await page.wait_for_timeout(10000)
            
            # Persistent check for login loops
            for i in range(5):
                print(f"Check {i}: Current URL: {page.url}")
                if "dashboard" in page.url:
                    return True
                if "github.com/login" in page.url:
                    print("Action: Re-entering GitHub Password...")
                    await page.fill("#password", "Nia@Atavism2026!")
                    await page.click("input[type='submit']")
                if "authorize" in page.url:
                    print("Action: Clicking Authorize...")
                    await page.evaluate("try { Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click(); } catch(e) {}")
                await page.wait_for_timeout(10000)
            return "dashboard" in page.url

        try:
            await github_login()
            success = await railway_auth()
            
            if success:
                print("Action: Fetching Final URL...")
                await page.goto("https://railway.com/dashboard")
                await page.wait_for_timeout(10000)
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(5000)
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(5000)
                final_url = await page.evaluate("Array.from(document.querySelectorAll('a')).find(l => l.href.includes('.up.railway.app')).href")
                print(f"RESULT_SUCCESS: {final_url}")
                await page.screenshot(path="ultimate_success.png")
            else:
                print("RESULT_FAIL: Stuck.")
                await page.screenshot(path="ultimate_fail.png")
        except Exception as e:
            print(f"RESULT_ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

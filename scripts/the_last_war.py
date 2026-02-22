
import asyncio
import sys
from playwright.async_api import async_playwright

async def run(code):
    async with async_playwright() as p:
        # Use a persistent context to ensure the session is truly kept
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_persistent_data",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(60000)
        
        try:
            # 1. GitHub login
            print("1. GitHub login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(3000)
            
            # 2FA
            if "verified-device" in page.url:
                print("2. 2FA...")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            # 2. Railway
            print("3. Railway login...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            # Click GitHub button
            await page.mouse.click(640, 480)
            await page.wait_for_timeout(20000) # Give it plenty of time
            
            # 3. Handle OAuth / Authorize
            print(f"Current URL: {page.url}")
            if "github.com" in page.url:
                print("Action: Authorizing or Re-authenticating...")
                # Try clicking authorize if it exists
                await page.evaluate("""
                    const btns = Array.from(document.querySelectorAll('button'));
                    const auth = btns.find(x => x.innerText.includes('Authorize'));
                    if (auth) auth.click();
                """)
                # Try filling password if asked
                if await page.query_selector("#password"):
                    await page.fill("#password", "Nia@Atavism2026!")
                    await page.click("input[type='submit']")
                await page.wait_for_timeout(20000)

            # 4. Final Dashboard Check
            print(f"Final URL check: {page.url}")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(15000)
            await page.screenshot(path="VERIFIED_DASHBOARD.png")
            
            text = await page.evaluate("document.body.innerText")
            with open("DASHBOARD_TEXT.txt", "w") as f:
                f.write(text)
            
            if "Nia-Link" in text:
                print("VICTORY.")
            else:
                print("STILL_FAILED.")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

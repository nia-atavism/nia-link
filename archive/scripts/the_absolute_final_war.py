
import asyncio
import sys
from playwright.async_api import async_playwright

async def run(code):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a fresh persistent context for this specific run
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(90000)
        
        try:
            # Step 1: Initial GitHub Login
            print("1. Initial GitHub login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            
            # Step 2: Handle First OTP
            if "verified-device" in page.url:
                print(f"Entering first OTP: {code}")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            print(f"First login phase URL: {page.url}")

            # Step 3: Railway Portal Entry
            print("2. Entering Railway...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            # Force click the button area
            await page.mouse.click(640, 480)
            
            # Step 4: Handle the Redirection & SECONDARY Verification
            print("3. Handling redirection chain...")
            for i in range(15):
                await page.wait_for_timeout(8000)
                url = page.url
                print(f"[{i}] {url}")
                
                if "dashboard" in url:
                    break
                
                # Case: GitHub asks for password again during OAuth
                if "github.com/login" in url:
                    print("Secondary Login Prompt. Filling...")
                    # Ensure login field is filled
                    if await page.is_visible("#login_field"):
                        await page.fill("#login_field", "linianrou1020@gmail.com")
                    await page.fill("#password", "Nia@Atavism2026!")
                    await page.click("input[type='submit']")
                
                # Case: GitHub asks for OTP AGAIN during OAuth
                if "verified-device" in url:
                    print("Secondary OTP Prompt! Trying same code...")
                    try:
                        await page.fill("#otp", code)
                        await page.keyboard.press("Enter")
                    except:
                        pass
                
                # Case: Authorization button
                if "authorize" in url:
                    print("Authorize Button detected. Clicking...")
                    await page.evaluate("try { Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click(); } catch(e) {}")

            # Step 5: Final Check
            if "dashboard" in page.url:
                print("SUCCESS: Logged in.")
                await page.goto("https://railway.com/dashboard")
                await page.wait_for_timeout(10000)
                
                # Select Nia-Link_v0.9
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(8000)
                
                # Settings
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(8000)
                
                # URL Harvest
                final_url = await page.evaluate("""
                    Array.from(document.querySelectorAll('a'))
                    .find(l => l.href.includes('.up.railway.app'))?.href
                """)
                print(f"VICTORY_URL: {final_url}")
                await page.screenshot(path="FINAL_MISSION_SUCCESS.png")
            else:
                print("FAILED.")
                await page.screenshot(path="FINAL_MISSION_FAIL.png")

        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

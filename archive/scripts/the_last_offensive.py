
import asyncio
import sys
from playwright.async_api import async_playwright

async def run(code):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(60000)
        
        try:
            # 1. Primary GitHub Login
            print("1. GitHub login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(3000)
            
            # Use current OTP
            if "verified-device" in page.url:
                print(f"Action: OTP entering {code}...")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            # 2. Go to Railway Login
            print("2. Railway portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(5000)
            print("Action: Clicking GitHub Login button area...")
            await page.mouse.click(640, 480)
            
            # 3. Handle specific secondary re-auth or authorize
            print("3. Monitoring flow...")
            for i in range(15):
                await page.wait_for_timeout(8000)
                print(f"[{i}] URL: {page.url}")
                
                if "dashboard" in page.url:
                    break
                
                # Check for secondary password prompt
                if "github.com/login" in page.url:
                    print("Action: Secondary password input...")
                    # IMPORTANT: Use a try block because context might change during navigation
                    try:
                        await page.fill("#password", "Nia@Atavism2026!")
                        await page.click("input[type='submit']")
                    except:
                        pass
                
                # Check for 2FA on the secondary login!
                if "verified-device" in page.url:
                    print("Action: OTP needed on secondary login. Entering same code...")
                    try:
                        await page.fill("#otp", code)
                        await page.keyboard.press("Enter")
                    except:
                        pass

                # Check for Authorize
                if "authorize" in page.url:
                    print("Action: Authorizing Railway...")
                    await page.evaluate("try { Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click(); } catch(e) {}")

            # 4. Dashboard success
            if "dashboard" in page.url:
                print("SUCCESS: Logged in.")
                await page.goto("https://railway.com/dashboard")
                await page.wait_for_timeout(10000)
                # Select Nia-Link_v0.9
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(5000)
                # Settings
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(8000)
                
                final_url = await page.evaluate("""
                    Array.from(document.querySelectorAll('a'))
                    .find(l => l.href.includes('.up.railway.app'))?.href
                """)
                print(f"LOCKED_URL: {final_url}")
                await page.screenshot(path="VICTORY_DASHBOARD.png")
            else:
                print("FAILED.")
                await page.screenshot(path="VICTORY_FAIL.png")

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

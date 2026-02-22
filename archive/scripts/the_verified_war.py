
import asyncio
import sys
from playwright.async_api import async_playwright

async def run(code):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a fresh persistent context
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(90000)
        
        try:
            # 1. GitHub Auth (Primary)
            print("1. GitHub login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            # DOUBLE CHECK PASSWORD IN LOGS (It was Nia@Atavism2026!)
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            
            if "verified-device" in page.url:
                print(f"Entering OTP: {code}")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            print(f"GitHub Logged in: {page.url}")

            # 2. Railway Entry
            print("2. Railway portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            print("Clicking login button...")
            await page.mouse.click(640, 480) # Force click center
            
            # 3. Handle redirection and potential secondary password prompts
            print("3. Redirection monitor...")
            for i in range(12):
                print(f"Step {i}: {page.url}")
                if "dashboard" in page.url:
                    break
                
                # Check for password prompt - using more specific selector
                pwd_input = await page.query_selector("input[type='password']")
                if pwd_input and "github.com/login" in page.url:
                    print("Secondary password prompt detected. Filling...")
                    await page.fill("input[type='password']", "Nia@Atavism2026!")
                    await page.click("input[type='submit']")
                    await page.wait_for_timeout(5000)
                
                # Check for Authorize button
                auth_btn = await page.query_selector("button:has-text('Authorize')")
                if auth_btn and "authorize" in page.url:
                    print("Authorization page detected. Clicking...")
                    await page.evaluate("const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')); if(b) b.click();")
                    await page.wait_for_timeout(5000)
                
                await page.wait_for_timeout(10000)

            # 4. Extraction
            if "dashboard" in page.url:
                print("4. Dashboard extraction...")
                await page.goto("https://railway.com/dashboard")
                await page.wait_for_timeout(10000)
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(5000)
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(5000)
                
                final_url = await page.evaluate("""
                    Array.from(document.querySelectorAll('a'))
                    .find(l => l.href.includes('.up.railway.app'))?.href
                """)
                print(f"VICTORY_URL: {final_url}")
                await page.screenshot(path="verified_final.png")
            else:
                print(f"FAILED: Stuck at {page.url}")
                await page.screenshot(path="verified_fail.png")

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))


import asyncio
import sys
from playwright.async_api import async_playwright

async def run(code):
    async with async_playwright() as p:
        # Use a fresh context to handle the login flow in one go
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
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
            
            # 2. 2FA
            if "verified-device" in page.url:
                print("2. 2FA entering...")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            # 3. Railway Login
            print("3. Railway login portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(5000)
            
            # Wait for button and click
            print("Clicking GitHub Button...")
            await page.mouse.click(640, 480)
            
            # 4. Handle Redirection Loop
            print("4. Monitoring URL changes...")
            for i in range(10):
                print(f"[{i}] URL: {page.url}")
                if "dashboard" in page.url:
                    break
                
                # If stuck at GitHub login during OAuth
                if "github.com/login" in page.url:
                    print("Prompted for GitHub password again...")
                    if await page.query_selector("#password"):
                        await page.fill("#password", "Nia@Atavism2026!")
                        await page.click("input[type='submit']")
                
                # If at authorization screen
                if "authorize" in page.url:
                    print("Clicking Authorize...")
                    await page.evaluate("const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')); if(b) b.click();")
                
                await page.wait_for_timeout(10000)

            # 5. Final Extraction
            print(f"Final URL: {page.url}")
            await page.screenshot(path="ULTIMATE_VICTORY.png")
            
            if "dashboard" in page.url:
                print("SUCCESS: In Dashboard.")
                # Get the link via direct navigation to project
                await page.goto("https://railway.com/dashboard")
                await page.wait_for_timeout(10000)
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(5000)
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(5000)
                final_url = await page.evaluate("Array.from(document.querySelectorAll('a')).find(l => l.href.includes('.up.railway.app')).href")
                print(f"LINK_FOUND: {final_url}")
            else:
                print("STILL_STUCK.")

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

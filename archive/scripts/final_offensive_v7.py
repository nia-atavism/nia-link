
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
            # 1. GitHub Auth
            print("Action: GitHub login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(3000)
            
            if "verified-device" in page.url:
                print(f"Action: OTP entering {code}...")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            # 2. Railway Auth
            print("Action: Railway portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(5000)
            print("Action: Clicking Login Button...")
            await page.mouse.click(640, 480)
            
            # 3. Redirection Loop with safety checks
            print("Action: Monitoring flow...")
            for i in range(12):
                await page.wait_for_timeout(10000)
                print(f"[{i}] {page.url}")
                
                if "dashboard" in page.url:
                    break
                
                # Check for secondary login
                if "github.com/login" in page.url:
                    print("Action: Handling Re-auth...")
                    pwd = await page.query_selector("#password")
                    if pwd:
                        await page.fill("#password", "Nia@Atavism2026!")
                        await page.click("input[type='submit']")
                
                # Check for authorize
                if "authorize" in page.url:
                    print("Action: Authorizing...")
                    await page.evaluate("const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')); if(b) b.click();")

            # 4. Success check
            if "dashboard" in page.url:
                print("Action: Accessing Project...")
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
                print(f"FOUND: {final_url}")
                await page.screenshot(path="OFFENSIVE_RESULT.png")
            else:
                print("Action: Failed to reach dashboard.")
                await page.screenshot(path="OFFENSIVE_FAIL.png")

        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

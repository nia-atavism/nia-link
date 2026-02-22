
import asyncio
import sys
from playwright.async_api import async_playwright

async def victory_code_run(code):
    async with async_playwright() as p:
        # Use a persistent context to handle the login flow in one go
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
            
            # 2. 2FA entering
            if "verified-device" in page.url or await page.locator("#otp").is_visible():
                print(f"2. 2FA entering {code}...")
                # GitHub might use #otp or name='otp'
                otp_field = page.locator("#otp")
                if await otp_field.is_hidden():
                    otp_field = page.locator("input[name='otp']")
                await otp_field.fill(code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            # 3. Railway Login portal
            print("3. Railway login portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(5000)
            
            # Wait for button and click center (GitHub button area)
            print("Action: Clicking GitHub Button...")
            await page.mouse.click(640, 480)
            
            # 4. Handle Redirection / Authorization Loop
            print("4. Monitoring flow...")
            for i in range(12):
                await page.wait_for_timeout(10000)
                print(f"[{i}] {page.url}")
                
                if "dashboard" in page.url:
                    break
                
                # Check for secondary login (GitHub re-auth)
                if "github.com/login" in page.url:
                    print("Action: Handling GitHub Re-auth...")
                    pwd_field = await page.query_selector("#password")
                    if pwd_field:
                        await page.fill("#password", "Nia@Atavism2026!")
                        await page.click("input[type='submit']")
                
                # Check for authorize button
                if "authorize" in page.url:
                    print("Action: Clicking Authorize...")
                    await page.evaluate("const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')); if(b) b.click();")

            # 5. Success check
            if "dashboard" in page.url:
                print("Action: Navigating to Project Detail...")
                await page.goto("https://railway.com/dashboard")
                await page.wait_for_timeout(10000)
                
                # Find Nia-Link_v0.9 link
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(8000)
                
                # Enter Settings
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(8000)
                await page.evaluate("window.scrollTo(0, 1000)")
                
                # Extract the public URL
                final_url = await page.evaluate("""
                    Array.from(document.querySelectorAll('a'))
                    .find(l => l.href.includes('.up.railway.app'))?.href
                """)
                print(f"FINAL_LOCKED_URL: {final_url}")
                await page.screenshot(path="FINAL_VICTORY_CLOUD.png")
                
                # Test the URL
                import httpx
                async with httpx.AsyncClient() as client:
                    try:
                        resp = await client.get(f"{final_url}/health", timeout=10.0)
                        print(f"Health Check: {resp.status_code} {resp.text}")
                    except Exception as e:
                        print(f"Health Check Failed: {e}")
            else:
                print("Action: Failed to reach dashboard.")
                await page.screenshot(path="FINAL_FAIL_DEBUG.png")

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(victory_code_run(sys.argv[1]))

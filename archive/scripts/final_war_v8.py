
import asyncio
import sys
from playwright.async_api import async_playwright

async def run(code):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a consistent user data dir
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(90000)

        try:
            # 1. GitHub
            print("Action: GitHub Login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            
            if "verified-device" in page.url:
                print(f"Action: 2FA {code}...")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            # 2. Railway
            print("Action: Railway Portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            print("Action: Clicking GitHub...")
            await page.mouse.click(640, 480) # Click center button
            
            # 3. Handle redirections
            for i in range(15):
                await page.wait_for_timeout(5000)
                print(f"[{i}] URL: {page.url}")
                
                if "dashboard" in page.url:
                    break
                
                if "github.com/login" in page.url:
                    print("Action: GitHub Re-Auth...")
                    # Check if login field is empty
                    is_empty = await page.evaluate("document.querySelector('#login_field')?.value === ''")
                    if is_empty:
                        await page.fill("#login_field", "linianrou1020@gmail.com")
                    await page.fill("#password", "Nia@Atavism2026!")
                    await page.click("input[type='submit']")
                
                if "authorize" in page.url:
                    print("Action: Authorize...")
                    await page.evaluate("try { Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click(); } catch(e) {}")

            if "dashboard" in page.url:
                print("SUCCESS: Logged in.")
                await page.goto("https://railway.com/dashboard")
                await page.wait_for_timeout(10000)
                
                # Enter Project
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(5000)
                
                # Check Domain in Settings
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(8000)
                await page.evaluate("window.scrollTo(0, 1000)")
                
                # Extract the first .up.railway.app link
                final_url = await page.evaluate("""
                    Array.from(document.querySelectorAll('a'))
                    .find(l => l.href.includes('.up.railway.app'))?.href
                """)
                print(f"VICTORY_URL: {final_url}")
                await page.screenshot(path="MISSION_ACCOMPLISHED.png")
            else:
                print("FAILED.")
                await page.screenshot(path="STILL_FAILED.png")

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

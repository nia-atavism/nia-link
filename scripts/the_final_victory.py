
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def the_final_victory(code):
    async with async_playwright() as p:
        # Use a fresh context to ensure no interference
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_timeout(60000)
        
        try:
            # 1. GitHub Login
            print("1. GitHub Login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            
            # 2. 2FA Check
            if "verified-device" in page.url or page.locator("#otp").is_visible():
                print(f"2. Entering 2FA: {code}")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            print(f"Logged into GitHub. URL: {page.url}")

            # 3. Railway Login
            print("3. Railway Portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            
            # Click GitHub Button using coordinates to bypass any weird DOM issues
            print("Clicking GitHub Login via coordinates...")
            await page.mouse.click(640, 480) 
            await page.wait_for_timeout(20000)

            # 4. Handle Authorize page if it appears
            if "github.com" in page.url and "authorize" in page.url:
                print("4. Authorizing...")
                await page.evaluate("Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click();")
                await page.wait_for_timeout(15000)

            # 5. Access Dashboard and get the link
            print("5. Inspection...")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(15000)
            
            # Capture evidence
            await page.screenshot(path="final_victory_evidence.png")
            text = await page.evaluate("document.body.innerText")
            with open("final_victory_dump.txt", "w") as f:
                f.write(text)

            if "Nia-Link" in text:
                print("SUCCESS: Nia-Link found on Dashboard.")
                # Attempt to find the URL
                links = await page.evaluate("""
                    Array.from(document.querySelectorAll('a'))
                    .filter(a => a.href.includes('.up.railway.app'))
                    .map(a => a.href)
                """)
                if links:
                    print(f"URLS_FOUND: {links}")
                else:
                    # Try to enter the project
                    await page.click("a:has-text('Nia-Link_v0.9')")
                    await page.wait_for_timeout(10000)
                    await page.click("button:has-text('Settings')")
                    await page.wait_for_timeout(8000)
                    url_final = await page.evaluate("Array.from(document.querySelectorAll('a')).find(l => l.href.includes('.up.railway.app')).href")
                    print(f"FINAL_LOCKED_URL: {url_final}")
            else:
                print(f"FAILED. Currently at: {page.url}")

        except Exception as e:
            print(f"ERROR: {e}")
            await page.screenshot(path="final_victory_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(the_final_victory(sys.argv[1]))

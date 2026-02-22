
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def run(code):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        
        try:
            # 1. GitHub
            print("Login GitHub...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            if "verified-device" in page.url:
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            # 2. Railway
            print("Railway Login...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            # Use mouse click on button
            await page.mouse.click(640, 480)
            await page.wait_for_timeout(15000)
            
            # 3. Handle re-auth loop
            for i in range(3):
                print(f"Loop {i}: {page.url}")
                if "dashboard" in page.url: break
                if "github.com/login" in page.url:
                    await page.fill("#password", "Nia@Atavism2026!")
                    await page.click("input[type='submit']")
                if "authorize" in page.url:
                    await page.evaluate("Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click()")
                await page.wait_for_timeout(10000)

            # 4. Final Data
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(10000)
            await page.screenshot(path="final_fix.png")
            
            # Find the Nia-Link project link
            href = await page.evaluate("""
                Array.from(document.querySelectorAll('a'))
                .find(a => a.innerText.includes('Nia-Link_v0.9'))?.href
            """)
            if href:
                print(f"Project URL: {href}")
                await page.goto(href)
                await page.wait_for_timeout(8000)
                # Find the public link
                final_url = await page.evaluate("""
                    Array.from(document.querySelectorAll('a'))
                    .find(l => l.href.includes('.up.railway.app'))?.href
                """)
                print(f"FOUND_SUCCESS: {final_url}")
            else:
                print("Project not found in dashboard.")

        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

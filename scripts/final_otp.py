
import asyncio
import sys
from playwright.async_api import async_playwright

async def run(code):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 1. GitHub
            print("GitHub...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(3000)
            
            if "verified-device" in page.url:
                print("2FA...")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            # 2. Railway
            print("Railway...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(5000)
            await page.mouse.click(640, 480) # Click GitHub
            await page.wait_for_timeout(10000)
            
            # Authorize
            if "authorize" in page.url:
                print("Authorize...")
                await page.evaluate("document.querySelector('button[type=submit]').click()")
                await page.wait_for_timeout(10000)
                
            # 3. Dashboard
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(10000)
            await page.screenshot(path="FINAL_DASHBOARD.png")
            
            # Extract links
            links = await page.evaluate("Array.from(document.querySelectorAll('a')).map(a => a.href)")
            with open("LINKS.txt", "w") as f:
                for l in links: f.write(l + "\n")
            print("Success.")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

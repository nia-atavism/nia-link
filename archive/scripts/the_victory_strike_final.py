
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def the_victory_strike_final(code):
    async with async_playwright() as p:
        # Use a fresh persistent context for this final attempt
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_victory_final",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_timeout(90000)
        
        try:
            # 1. GitHub Login
            print("1. GitHub login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(5000)
            
            # 2. 2FA Check
            if "verified-device" in page.url or await page.locator("#otp").is_visible():
                print(f"Entering 2FA Code: {code}")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            print(f"Logged into GitHub: {page.url}")

            # 3. Railway Login
            print("2. Railway login portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            
            # Force click the GitHub button area (centerish)
            print("Force clicking login button area...")
            await page.mouse.click(640, 480) 
            await page.wait_for_timeout(15000)

            # 4. Handle Authorize or Second Login
            print(f"Current URL after click: {page.url}")
            if "github.com/login" in page.url:
                print("Re-authenticating GitHub...")
                await page.fill("#password", "Nia@Atavism2026!")
                await page.click("input[type='submit']")
                await page.wait_for_timeout(15000)

            if "oauth/authorize" in page.url:
                print("Clicking Authorize...")
                await page.evaluate("try { Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click(); } catch(e) {}")
                await page.wait_for_timeout(15000)

            # 5. Dashboard Inspection
            print(f"Final destination check: {page.url}")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(15000)
            
            await page.screenshot(path="victory_final_result.png")
            text = await page.evaluate("document.body.innerText")
            
            if "Nia-Link" in text:
                print("VICTORY: Project found.")
                # Get the link
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(8000)
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(8000)
                url_final = await page.evaluate("Array.from(document.querySelectorAll('a')).find(l => l.href.includes('.up.railway.app')).href")
                print(f"FINAL_URL: {url_final}")
                with open("final_success_url.txt", "w") as f:
                    f.write(url_final)
            else:
                print(f"FAILED: Project not visible on {page.url}")
                with open("victory_fail_dump.txt", "w") as f:
                    f.write(text)

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
            await page.screenshot(path="victory_error.png")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(the_victory_strike_final(sys.argv[1]))

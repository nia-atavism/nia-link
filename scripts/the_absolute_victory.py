
import asyncio
import sys
import base64
from playwright.async_api import async_playwright

async def the_absolute_victory(code):
    async with async_playwright() as p:
        # Use a persistent context to make sure sessions are kept
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_persistent_victory",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_timeout(120000)
        
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
                print(f"Entering 2FA: {code}")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            print(f"Logged into GitHub: {page.url}")

            # 3. Railway Login
            print("2. Railway portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            
            # Force click the GitHub button area
            print("Force clicking login button area...")
            await page.mouse.click(640, 480) 
            await page.wait_for_timeout(15000)

            # 4. Handle SECONDARY GitHub Login (The current block!)
            if "github.com/login" in page.url:
                print("GitHub requested re-authentication. Filling again...")
                # Note: username might be prefilled or hidden
                user_field = await page.query_selector("#login_field")
                if user_field:
                    await page.fill("#login_field", "linianrou1020@gmail.com")
                await page.fill("#password", "Nia@Atavism2026!")
                await page.click("input[type='submit']")
                await page.wait_for_timeout(15000)

            # 5. Handle Authorize
            if "oauth/authorize" in page.url:
                print("Clicking Authorize...")
                await page.evaluate("try { Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')).click(); } catch(e) {}")
                await page.wait_for_timeout(15000)

            # 6. Final Dashboard Check
            print(f"Final destination: {page.url}")
            await page.goto("https://railway.com/dashboard")
            await page.wait_for_timeout(15000)
            
            await page.screenshot(path="absolute_victory_final.png")
            text = await page.evaluate("document.body.innerText")
            with open("absolute_victory_dump.txt", "w") as f:
                f.write(text)

            if "Nia-Link" in text:
                print("ABSOLUTE_VICTORY: SUCCESS.")
                # Attempt to get the settings URL
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(5000)
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(5000)
                url_final = await page.evaluate("Array.from(document.querySelectorAll('a')).find(l => l.href.includes('.up.railway.app')).href")
                print(f"FINAL_URL: {url_final}")
            else:
                print(f"FAILED. Stuck at: {page.url}")

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
            await page.screenshot(path="absolute_victory_error.png")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(the_absolute_victory(sys.argv[1]))

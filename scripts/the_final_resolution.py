
import asyncio
import sys
from playwright.async_api import async_playwright

async def run(code):
    async with async_playwright() as p:
        # Use a fresh persistent context to avoid session overlap
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_final_resolution",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(60000)
        
        try:
            # 1. GitHub Auth (Primary)
            print("1. GitHub login...")
            await page.goto("https://github.com/login")
            await page.fill("#login_field", "linianrou1020@gmail.com")
            await page.fill("#password", "Nia@Atavism2026!")
            await page.click("input[type='submit']")
            await page.wait_for_timeout(3000)
            
            if "verified-device" in page.url:
                print(f"Entering OTP: {code}")
                await page.fill("#otp", code)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
            
            # 2. Railway Entry
            print("2. Railway portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            print("Clicking login button...")
            await page.mouse.click(640, 480) # Force click center
            
            # 3. Handle the dreaded re-authentication loop
            print("3. Redirection monitor...")
            for i in range(12):
                print(f"Step {i}: {page.url}")
                if "dashboard" in page.url:
                    break
                
                # If stuck at GitHub login during OAuth flow
                if "github.com/login" in page.url:
                    print("Re-filling credentials for OAuth...")
                    # MUST check if field is empty
                    val = await page.input_value("#login_field")
                    if not val:
                        await page.fill("#login_field", "linianrou1020@gmail.com")
                    await page.fill("#password", "Nia@Atavism2026!")
                    await page.click("input[type='submit']")
                
                # If at authorization screen
                if "authorize" in page.url:
                    print("Granting Authorization...")
                    await page.evaluate("const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')); if(b) b.click();")
                
                await page.wait_for_timeout(10000)

            # 4. Final verification and extraction
            if "dashboard" in page.url:
                print("4. Inspection...")
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
                print(f"RESOLUTION_SUCCESS: {final_url}")
                await page.screenshot(path="final_resolution.png")
            else:
                print(f"RESOLUTION_FAILED: Stuck at {page.url}")
                await page.screenshot(path="final_resolution_fail.png")

        except Exception as e:
            print(f"RESOLUTION_ERROR: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

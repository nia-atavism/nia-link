
import asyncio
import sys
from playwright.async_api import async_playwright

async def run(code):
    async with async_playwright() as p:
        # Use a fresh persistent context to avoid any interference
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_victory_final_attempt",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(60000)
        
        try:
            # 1. GitHub Primary Login
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
            
            # 2. Railway Portal Entry
            print("Action: Railway portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(5000)
            # Click GitHub button using coordinate
            await page.mouse.click(640, 480)
            
            # 3. Handle the Redirection Loop
            print("Action: Monitoring flow...")
            for i in range(12):
                await page.wait_for_timeout(10000)
                print(f"[{i}] {page.url}")
                
                if "dashboard" in page.url:
                    break
                
                # Handling secondary GitHub login (crucial)
                if "github.com/login" in page.url:
                    print("Action: Secondary Login detected...")
                    # Ensure login field is filled
                    val = await page.input_value("#login_field")
                    if not val:
                        await page.fill("#login_field", "linianrou1020@gmail.com")
                    await page.fill("#password", "Nia@Atavism2026!")
                    await page.click("input[type='submit']")
                
                # Handling Authorize button
                if "authorize" in page.url:
                    print("Action: Authorizing Railway...")
                    await page.evaluate("const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')); if(b) b.click();")

            # 4. Final Success Verification
            if "dashboard" in page.url:
                print("Action: Dashboard Success.")
                await page.goto("https://railway.com/dashboard")
                await page.wait_for_timeout(10000)
                
                # Find project Nia-Link_v0.9
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(5000)
                
                # Settings to find URL
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(5000)
                
                final_url = await page.evaluate("""
                    Array.from(document.querySelectorAll('a'))
                    .find(l => l.href.includes('.up.railway.app'))?.href
                """)
                print(f"CLOUD_SUCCESS_URL: {final_url}")
                await page.screenshot(path="SUCCESS_CLOUD.png")
            else:
                print("Action: Failed to reach dashboard.")
                await page.screenshot(path="FAIL_CLOUD.png")

        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

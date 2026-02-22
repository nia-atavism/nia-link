
import asyncio
import sys
from playwright.async_api import async_playwright

async def the_complete_victory(code):
    async with async_playwright() as p:
        # Use a fresh persistent context to avoid session overlap but keep it during this run
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./railway_complete_victory",
            headless=True,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_navigation_timeout(90000)
        
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
            
            print(f"GitHub Logged in: {page.url}")

            # 2. Railway Entry
            print("2. Railway portal...")
            await page.goto("https://railway.com/login")
            await page.wait_for_timeout(10000)
            print("Clicking login button...")
            await page.mouse.click(640, 480) # Force click center
            
            # 3. Handle redirection and potential secondary password prompts
            print("3. Redirection monitor...")
            for i in range(12):
                await page.wait_for_timeout(10000)
                print(f"Step {i}: {page.url}")
                if "dashboard" in page.url:
                    break
                
                # Check for password prompt
                if "github.com/login" in page.url:
                    print("Secondary GitHub prompt detected.")
                    # IMPORTANT: Fill BOTH fields if they exist and are empty
                    user_val = await page.input_value("#login_field") if await page.query_selector("#login_field") else "filled"
                    if not user_val:
                        print("Filling email...")
                        await page.fill("#login_field", "linianrou1020@gmail.com")
                    
                    pwd_input = await page.query_selector("#password")
                    if pwd_input:
                        print("Filling password...")
                        await page.fill("#password", "Nia@Atavism2026!")
                        await page.click("input[type='submit']")
                
                # Check for Authorize button
                if "authorize" in page.url:
                    print("Authorization page detected. Clicking...")
                    await page.evaluate("const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('Authorize')); if(b) b.click();")
                
            # 4. Final Verification
            if "dashboard" in page.url:
                print("4. Accessing Dashboard...")
                await page.goto("https://railway.com/dashboard")
                await page.wait_for_timeout(10000)
                
                # Find Nia-Link_v0.9
                await page.click("a:has-text('Nia-Link_v0.9')")
                await page.wait_for_timeout(5000)
                
                # Get the link
                await page.click("button:has-text('Settings')")
                await page.wait_for_timeout(5000)
                final_url = await page.evaluate("""
                    Array.from(document.querySelectorAll('a'))
                    .find(l => l.href.includes('.up.railway.app'))?.href
                """)
                print(f"COMPLETE_SUCCESS: {final_url}")
                await page.screenshot(path="complete_victory_final.png")
            else:
                print("FAILED.")
                await page.screenshot(path="complete_victory_fail.png")

        except Exception as e:
            print(f"CRITICAL_ERROR: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(the_complete_victory(sys.argv[1]))

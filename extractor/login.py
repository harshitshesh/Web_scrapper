from playwright.sync_api import sync_playwright
import os

os.makedirs("screenshots", exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.goto("https://white-cliff-0bca3ed00.1.azurestaticapps.net/")
    page.wait_for_timeout(2000)
    page.screenshot(path="screenshots/01_landing_page.png")
    
    page.click("text=Getting Started")
    page.wait_for_timeout(2000)
    page.screenshot(path="screenshots/02_login_page.png")
    
    page.fill("input[type='email']", "admin@gmail.com")
    page.fill("input[type='password']", "password")
    page.screenshot(path="screenshots/03_filled_login.png")
    
    page.get_by_role("button", name="Login").click()
    page.wait_for_selector("text=My Applications", timeout=15000)
    page.wait_for_selector("text=PNW-", timeout=15000)
    page.wait_for_timeout(2000)
    
    page.screenshot(path="screenshots/04_dashboard.png")
    print("Current URL:", page.url)
    print("Login successful!" if "dashboard" in page.url else "Login may have failed")
    
    browser.close()
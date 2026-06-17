from playwright.sync_api import sync_playwright


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://white-cliff-0bca3ed00.1.azurestaticapps.net/")
    page.wait_for_timeout(3000)  # 3 second wait taaki page load ho jaye
    page.screenshot(path="extractor/screenshots/landing_page.png")
    print("Screenshot taken!")
    browser.close()
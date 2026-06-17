from playwright.sync_api import sync_playwright
import json

from datetime import datetime, timezone

extracted_data = []


def log_component(page_url, component_type, selector, text, screenshot_path):
    extracted_data.append({
        "page_url": page_url,
        "component_type": component_type,
        "component_selector": selector,
        "actual_text_content": text,
        "expected_text_content": None,  
        "guideline_reference": None,    
        "discrepancy_flag": None,        
        "discrepancy_reason": None,
        "screenshot_path": screenshot_path,
        "retrieved_at": datetime.now(timezone.utc).isoformat()
    })

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # ---- LOGIN ----
    page.goto("https://white-cliff-0bca3ed00.1.azurestaticapps.net/")
    page.wait_for_timeout(2000)
    page.click("text=Getting Started")
    page.wait_for_timeout(2000)
    page.fill("input[placeholder='m@example.com']", "admin@gmail.com")
    page.fill("input[type='password']", "password")
    page.get_by_role("button", name="Login").click()
    page.wait_for_selector("table tbody tr", timeout=15000)
    page.wait_for_timeout(1500)


    page_url = "/dashboard/my-applications"
    screenshot_path = "screenshots/my_applications.png"
    page.screenshot(path=screenshot_path)

  
    heading = page.locator("h1, h2").first.inner_text()
    log_component(page_url, "heading", "h1/h2", heading, screenshot_path)

    
    buttons = page.locator("button").all_inner_texts()
    for i, btn_text in enumerate(buttons):
        if btn_text.strip():  # empty buttons skip karo
            log_component(page_url, "button", f"button[{i}]", btn_text, screenshot_path)

    
    headers = page.locator("table thead th").all_inner_texts()
    log_component(page_url, "table_headers", "table thead th", headers, screenshot_path)

    browser.close()


with open("reports/dashboard_data.json", "w", encoding="utf-8") as f:
    json.dump(extracted_data, f, indent=4, ensure_ascii=False)

print(f"Extracted {len(extracted_data)} components. Saved to reports/dashboard_data.json")
    
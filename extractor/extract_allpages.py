from playwright.sync_api import sync_playwright
import json

from datetime import datetime, timezone



extracted_data = []
coverage_log = []  

BASE_URL = "https://white-cliff-0bca3ed00.1.azurestaticapps.net/"


PAGES_TO_EXTRACT = [
    {"name": "My Applications", "expected_url": "/dashboard/my-applications", "nav_text": "My Applications"},
    {"name": "Facilities", "expected_url": "/dashboard/facilities", "nav_text": "Facilities"},
    {"name": "Action Items", "expected_url": "/dashboard/action-items", "nav_text": "Action Items"},
    {"name": "User Management", "expected_url": "/dashboard/user-management", "nav_text": "User Management"},
    {"name": "Announcements", "expected_url": "/dashboard/announcements", "nav_text": "Announcements"},
    {"name": "Settings", "expected_url": "/dashboard/settings", "nav_text": "Settings"},
    {"name": "FAQs", "expected_url": "/dashboard/faqs", "nav_text": "FAQs"},
    {"name": "Tickets", "expected_url": "/dashboard/tickets", "nav_text": "Tickets"},
    {"name": "Contact", "expected_url": "/dashboard/contact", "nav_text": "Contact"},
]


def log_component(page_url, component_type, selector, text, screenshot_path):
    """Appends one schema-compliant record. Fields the agent fills later are left None."""
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


def extract_current_page(page, page_url, screenshot_path):
    """Pulls heading, buttons, and table headers from whatever page is currently loaded."""
    component_count = 0

    # Heading
    try:
        heading = page.locator("h1, h2").first.inner_text(timeout=3000)
        log_component(page_url, "heading", "h1/h2", heading, screenshot_path)
        component_count += 1
    except Exception as e:
        print(f"    [warn] no heading found: {e}")

    # Buttons
    try:
        buttons = page.locator("button").all_inner_texts()
        for i, btn_text in enumerate(buttons):
            if btn_text.strip():
                log_component(page_url, "button", f"button[{i}]", btn_text, screenshot_path)
                component_count += 1
    except Exception as e:
        print(f"    [warn] button extraction failed: {e}")

   
    try:
        headers = page.locator("table thead th").all_inner_texts()
        if headers:
            log_component(page_url, "table_headers", "table thead th", headers, screenshot_path)
            component_count += 1
    except Exception as e:
        print(f"    [warn] table header extraction failed: {e}")

    return component_count


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # ---------- LOGIN ----------
    print("Logging in...")
    page.goto(BASE_URL)
    page.wait_for_timeout(2000)
    page.click("text=Getting Started")
    page.wait_for_timeout(2000)
    page.fill("input[placeholder='m@example.com']", "admin@gmail.com")
    page.fill("input[type='password']", "password")
    page.get_by_role("button", name="Login").click()
    page.wait_for_selector("table tbody tr", timeout=15000)
    page.wait_for_timeout(1500)
    print("Login successful. Current URL:", page.url)

    print("\nExtracting: My Applications (default landing page after login)")
    screenshot_path = "screenshots/my_applications.png"
    page.screenshot(path=screenshot_path)
    count = extract_current_page(page, "/dashboard/my-applications", screenshot_path)
    coverage_log.append({"page": "My Applications", "status": "success", "components_found": count})
    print(f"  -> {count} components extracted")

    for entry in PAGES_TO_EXTRACT[1:]: 
        name = entry["name"]
        expected_url = entry["expected_url"]
        nav_text = entry["nav_text"]

        print(f"\nExtracting: {name}")
        try:
            page.click(f"text={nav_text}", timeout=8000)
            page.wait_for_timeout(2000)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)  # buffer for any async data

            safe_name = name.lower().replace(" ", "_")
            screenshot_path = f"screenshots/{safe_name}.png"
            page.screenshot(path=screenshot_path)

            count = extract_current_page(page, expected_url, screenshot_path)
            coverage_log.append({"page": name, "status": "success", "components_found": count})
            print(f"  -> {count} components extracted. Current URL: {page.url}")

        except Exception as e:
            print(f"  [FAILED] Could not extract {name}: {e}")
            coverage_log.append({"page": name, "status": "failed", "error": str(e), "components_found": 0})
            # Take a screenshot anyway for debugging the failure
            try:
                page.screenshot(path=f"screenshots/FAILED_{name.lower().replace(' ', '_')}.png")
            except Exception:
                pass

    browser.close()

# ---------- SAVE OUTPUTS ----------
with open("reports/extracted_data.json", "w", encoding="utf-8") as f:
    json.dump(extracted_data, f, indent=4, ensure_ascii=False)

with open("reports/coverage_report.json", "w", encoding="utf-8") as f:
    json.dump(coverage_log, f, indent=4, ensure_ascii=False)

print(f"\n{'='*50}")
print(f"DONE. Total components extracted: {len(extracted_data)}")
print(f"Pages succeeded: {sum(1 for c in coverage_log if c['status']=='success')}/{len(coverage_log)}")
print("Saved: report/extracted_data.json, report/coverage_report.json")
import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = BASE_DIR / "Screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:5173"

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--window-size=1600,1000")
opts.add_argument("--disable-gpu")
opts.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=opts)

try:
    print(f"Navigating to {URL}...")
    driver.get(URL)
    time.sleep(2)

    # 1. Verify Landing Page Loaded
    landing_view = driver.find_element(By.ID, "landing-view")
    assert landing_view.is_displayed(), "Landing view should be visible on initial load"
    print("[OK] Landing view is visible")

    page_source = driver.page_source.lower()

    # 2. Verify removals
    assert "example cases · physician signs every report" not in page_source, "Found 'example cases · physician signs every report'"
    assert "example cases" not in page_source, "Found 'example cases'"
    assert "physician signs every report" not in page_source, "Found 'physician signs every report'"
    assert "social media" not in page_source, "Found 'social media'"
    assert "collaboration" not in page_source, "Found 'collaboration'"
    print("[OK] Removals verified: 'Example Cases', 'Physician signs every report', 'Social Media', and 'Collaboration' are completely absent.")

    # Save screenshot of landing page
    landing_screenshot = SCREENSHOTS_DIR / "landing_page_updated.png"
    driver.save_screenshot(str(landing_screenshot))
    print(f"[OK] Saved landing screenshot to {landing_screenshot}")

    # 3. Test "Request a demo" -> Immediate access to workspace
    req_demo_btn = driver.find_element(By.ID, "btn-top-demo")
    print("Clicking 'Request a demo' in top navigation...")
    req_demo_btn.click()
    time.sleep(1.5)

    root_view = driver.find_element(By.ID, "root")
    assert root_view.is_displayed(), "#root should be visible after clicking Request a demo"
    assert not landing_view.is_displayed(), "#landing-view should be hidden after entering portal"
    print("[OK] Immediate portal transition succeeded: #root is visible, #landing-view is hidden")

    # Verify workspace loaded
    wait = WebDriverWait(driver, 5)
    intake_elem = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Intake & Triage')]")))
    assert intake_elem.is_displayed(), "Workspace 'Intake & Triage' tab should be visible"
    print("[OK] Virtual Hospital workspace loaded successfully!")

    workspace_screenshot = SCREENSHOTS_DIR / "workspace_entered_from_demo.png"
    driver.save_screenshot(str(workspace_screenshot))
    print(f"[OK] Saved workspace screenshot to {workspace_screenshot}")

    # 4. Test return to landing page
    back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Landing Page')]")
    print("Clicking Landing Page button to return...")
    back_btn.click()
    time.sleep(1)

    assert landing_view.is_displayed(), "#landing-view should be visible after returning"
    assert not root_view.is_displayed(), "#root should be hidden after returning"
    print("[OK] Return to landing page succeeded!")

    # 5. Test Demo section button inside #demo
    enter_btn = driver.find_element(By.ID, "btn-enter-hospital")
    print("Clicking 'Enter Virtual Hospital Demo' in Demo section...")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", enter_btn)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", enter_btn)
    time.sleep(1)

    assert root_view.is_displayed(), "#root should be visible after clicking demo section enter button"
    print("[OK] Demo section immediate access button succeeded!")

    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

finally:
    driver.quit()

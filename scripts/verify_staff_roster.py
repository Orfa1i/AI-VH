import time
import shutil
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = BASE_DIR / "Screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR = Path(r"C:\Users\PCD\.gemini\antigravity-cli\brain\17f22c14-b8f7-4171-b34f-c13b0184026f")
URL = "http://localhost:5173"

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--window-size=1600,1100")
opts.add_argument("--disable-gpu")
opts.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=opts)

try:
    print(f"Navigating to {URL}...")
    driver.get(URL)
    time.sleep(2)

    # 1. Enter portal from landing page via #btn-top-demo
    try:
        demo_btn = driver.find_element(By.ID, "btn-top-demo")
        demo_btn.click()
        print("[OK] Clicked #btn-top-demo to enter portal")
        time.sleep(1.5)
    except Exception as e:
        print("btn-top-demo not clicked:", e)

    # 2. Wait for workspace root
    wait = WebDriverWait(driver, 5)
    root = wait.until(EC.visibility_of_element_located((By.ID, "root")))
    print("[OK] Workspace #root visible")

    # 3. Find and click the Staff Roster tab in the top navigation
    staff_tab = driver.find_element(By.XPATH, "//button[contains(., 'Staff') or contains(., 'Staff Roster')]")
    driver.execute_script("arguments[0].click();", staff_tab)
    print("[OK] Clicked Staff tab")
    time.sleep(2)

    # 4. Save screenshot of the workspace with Staff Roster rendered
    screenshot_path = SCREENSHOTS_DIR / "staff_roster_verified.png"
    driver.save_screenshot(str(screenshot_path))
    print(f"[OK] Saved screenshot to {screenshot_path}")

    # Copy to artifacts directory
    artifact_screenshot = ARTIFACTS_DIR / "staff-roster-verified.png"
    shutil.copy2(screenshot_path, artifact_screenshot)
    print(f"[OK] Mirrored screenshot to {artifact_screenshot}")

    # 5. Switch to the Staff Roster iframe and inspect elements
    iframe = driver.find_element(By.XPATH, "//iframe[@title='Virtual Hospital Staff Roster']")
    driver.switch_to.frame(iframe)

    agents = driver.find_elements(By.CSS_SELECTOR, ".agent")
    print(f"[OK] Found {len(agents)} specialist agent cards in staff roster iframe")
    assert len(agents) == 7, f"Expected 7 specialist agents, found {len(agents)}"

    for a in agents:
        name = a.find_element(By.TAG_NAME, "h2").text
        status = a.find_element(By.CSS_SELECTOR, ".status").text
        book = a.find_element(By.CSS_SELECTOR, ".facts dd").text
        print(f"  - Agent: {name} | Status: {status} | Reads: {book}")

    # Check the "Add a specialist agent" card
    add_btn = driver.find_element(By.CSS_SELECTOR, ".add")
    assert add_btn.is_displayed(), "Add specialist agent card should be displayed"
    print("[OK] 'Add a specialist agent' card is displayed")

    # Check filter buttons
    filters = driver.find_elements(By.CSS_SELECTOR, "#filters button")
    assert len(filters) == 4, f"Expected 4 filter buttons, found {len(filters)}"
    print(f"[OK] Found {len(filters)} filter buttons: {[f.text for f in filters]}")

    driver.switch_to.default_content()
    print("[SUCCESS] Staff Roster page verification complete and 100% passing!")

finally:
    driver.quit()

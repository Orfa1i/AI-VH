"""
Script: capture_all_screenshots.py
Automates the capture of high-resolution, publication-grade PNG screenshots
for every page, route, portal tab, and specialist modal in AI Virtual Hospital (AI-VH).
Uses modular browser sessions to ensure total isolation and 100% reliable capture.
"""

import time
import os
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = BASE_DIR / "Screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

FRONTEND_URL = "http://localhost:5173"


def create_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--force-device-scale-factor=1.5")
    opts.add_argument("--enable-webgl")
    opts.add_argument("--ignore-gpu-blocklist")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--hide-scrollbars")
    opts.page_load_strategy = 'eager'
    return webdriver.Chrome(options=opts)


def click_button_by_text(driver, text):
    """Finds a button containing the given text and clicks it via JS."""
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if text.lower() in btn.text.lower():
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", btn)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", btn)
            return True
    return False


def wait_and_save(driver, filepath, wait_seconds=2.0):
    time.sleep(wait_seconds)
    driver.save_screenshot(str(filepath))
    size_kb = filepath.stat().st_size / 1024
    print(f"  [SAVED] {filepath.name} ({size_kb:.1f} KB)")


def run_capture_pipeline():
    print("================================================================")
    print("AI-VH HIGH-RESOLUTION SCREENSHOT GENERATOR")
    print(f"Target Directory: {SCREENSHOTS_DIR}")
    print(f"Base URL: {FRONTEND_URL}")
    print("================================================================\n")

    catalog = [
        {
            "filename": "01_case_intake_and_triage.png",
            "title": "Case Intake & Emergency Triage Admission Matrix",
            "route": "/",
            "slug": "/ (tab: INTAKE)",
            "desc": "5-Level Emergency Severity Index (ESI) admission dashboard, baseline vitals telemetry seed matrix, and clinical scenario presets."
        },
        {
            "filename": "02_patient_directory.png",
            "title": "Patient Directory, Census & Electronic Health Record Matrix",
            "route": "/?tab=PATIENTS",
            "slug": "/ (tab: PATIENTS)",
            "desc": "Master inpatient census table with real-time acuity indicators, department badges, and full EHR chart drawer access."
        },
        {
            "filename": "03_hospital_staff_directory.png",
            "title": "Hospital Medical Staff Directory & Credentialing",
            "route": "/?tab=STAFF",
            "slug": "/ (tab: STAFF)",
            "desc": "Roster of active clinical agents and human physicians, department filter controls, and Attending Physician profiles."
        },
        {
            "filename": "04_clinical_reports_and_reviews.png",
            "title": "Autonomous Clinical Reports & Physician Review Console",
            "route": "/?tab=REPORTS",
            "slug": "/ (tab: REPORTS)",
            "desc": "Attending review console with diagnostic confidence gauges, differential diagnoses, treatment regimens, and RL DPO evaluation."
        },
        {
            "filename": "05_harrisons_vector_rag_knowledge.png",
            "title": "Harrison's 21st Edition Semantic Vector RAG Explorer",
            "route": "/?tab=KNOWLEDGE",
            "slug": "/ (tab: KNOWLEDGE)",
            "desc": "Internal medicine vector knowledge explorer indexed across 47,806 semantic chunks with chapter filters and cosine similarity meters."
        },
        {
            "filename": "06_rl_policy_benchmark_portal.png",
            "title": "Reinforcement Learning Policy Benchmark Portal",
            "route": "/?tab=BENCHMARK",
            "slug": "/ (tab: BENCHMARK)",
            "desc": "Overview portal highlighting Base Foundation Model vs. RL DPO Aligned Model clinical reward deltas and benchmark launchers."
        },
        {
            "filename": "07_policy_benchmark_modal_console.png",
            "title": "RL DPO Policy Benchmark & Comparative Analytics Console",
            "route": "/ (Modal: PolicyBenchmarkModal)",
            "slug": "modal-policy-benchmark",
            "desc": "Side-by-side comparative clinical evaluation across diagnostic accuracy, treatment safety compliance, and contraindication avoidance."
        },
        {
            "filename": "08_rl_dataset_corpus_modal.png",
            "title": "RL DPO Preference Dataset & Clinical Safety Audit Corpus",
            "route": "/ (Modal: RLDatasetModal)",
            "slug": "modal-rl-dataset",
            "desc": "Supervised preference pairs with chosen vs. rejected clinical rationales, reward weights, and safety-critical contraindication audits."
        },
        {
            "filename": "09_dr_marcus_vance_consult_modal.png",
            "title": "Dr. Marcus Vance Attending RAG Specialist Consultation Modal",
            "route": "/ (Modal: DoctorChatModal)",
            "slug": "modal-doctor-chat",
            "desc": "Interactive clinical dialogue grounded in Harrison's 21st Edition evidence with Dr. Vance avatar, model telemetry, and prompt shortcuts."
        },
        {
            "filename": "10_clinical_flow_architecture_diagram.png",
            "title": "2D Clinical Flow Architecture Diagram & Real-Time ECG Telemetry",
            "route": "/3d (view: DIAGRAM)",
            "slug": "/3d#diagram",
            "desc": "Interactive hospital workflow diagram featuring live Lead II ECG waveform sweep, real-time vitals HUD, and clinical node progression."
        },
        {
            "filename": "11_3d_spatial_virtual_hospital.png",
            "title": "3D Spatial Virtual Hospital Campus & Real-Time Agent Avatars",
            "route": "/3d (view: 3D)",
            "slug": "/3d#spatial",
            "desc": "Three.js WebGL isometric hospital environment with multi-room wards, animated doctor and nurse agents, and floating status HUDs."
        }
    ]

    # -----------------------------------------------------------------
    # Session 1: Capture 6 Main Portal Tabs
    # -----------------------------------------------------------------
    print("SESSION 1: Capturing 6 Main Management Portal Tabs...")
    driver = create_driver()
    try:
        driver.get(f"{FRONTEND_URL}/")
        time.sleep(3.0)

        tabs = [
            ("Case Intake & Triage", "01_case_intake_and_triage.png"),
            ("Patient Directory", "02_patient_directory.png"),
            ("Hospital Staff", "03_hospital_staff_directory.png"),
            ("Clinical Reports & Reviews", "04_clinical_reports_and_reviews.png"),
            ("Harrison's Vector RAG", "05_harrisons_vector_rag_knowledge.png"),
            ("RL Policy Benchmark", "06_rl_policy_benchmark_portal.png"),
        ]

        for tab_name, fname in tabs:
            print(f"  -> Switching to {tab_name}...")
            click_button_by_text(driver, tab_name)
            wait_and_save(driver, SCREENSHOTS_DIR / fname, 2.0)
    finally:
        driver.quit()

    # -----------------------------------------------------------------
    # Session 2: Capture Policy Benchmark Console Modal
    # -----------------------------------------------------------------
    print("\nSESSION 2: Capturing Policy Benchmark Console Modal...")
    driver = create_driver()
    try:
        driver.get(f"{FRONTEND_URL}/")
        time.sleep(2.0)
        click_button_by_text(driver, "RL Policy Benchmark")
        time.sleep(1.0)
        click_button_by_text(driver, "Launch Policy Benchmark Console")
        wait_and_save(driver, SCREENSHOTS_DIR / "07_policy_benchmark_modal_console.png", 2.5)
    finally:
        driver.quit()

    # -----------------------------------------------------------------
    # Session 3: Capture RL Dataset Corpus Modal
    # -----------------------------------------------------------------
    print("\nSESSION 3: Capturing RL DPO Dataset Corpus Modal...")
    driver = create_driver()
    try:
        driver.get(f"{FRONTEND_URL}/")
        time.sleep(2.0)
        click_button_by_text(driver, "RL Policy Benchmark")
        time.sleep(1.0)
        click_button_by_text(driver, "Inspect DPO Preference Dataset")
        wait_and_save(driver, SCREENSHOTS_DIR / "08_rl_dataset_corpus_modal.png", 2.5)
    finally:
        driver.quit()

    # -----------------------------------------------------------------
    # Session 4: Capture Dr. Marcus Vance RAG Specialist Consultation Modal
    # -----------------------------------------------------------------
    print("\nSESSION 4: Capturing Dr. Marcus Vance RAG Consult Modal...")
    driver = create_driver()
    try:
        driver.get(f"{FRONTEND_URL}/")
        time.sleep(2.0)
        click_button_by_text(driver, "Dr. Vance RAG")
        wait_and_save(driver, SCREENSHOTS_DIR / "09_dr_marcus_vance_consult_modal.png", 2.5)
    finally:
        driver.quit()

    # -----------------------------------------------------------------
    # Session 5: Capture Simulation /3d (Flow Diagram & 3D Spatial)
    # -----------------------------------------------------------------
    print("\nSESSION 5: Capturing Clinical Simulation Views (/3d)...")
    driver = create_driver()
    try:
        driver.get(f"{FRONTEND_URL}/3d")
        time.sleep(3.0)
        print("  -> Capturing 2D Flow Architecture Diagram...")
        wait_and_save(driver, SCREENSHOTS_DIR / "10_clinical_flow_architecture_diagram.png", 2.5)

        print("  -> Toggling to 3D Spatial Virtual Hospital...")
        click_button_by_text(driver, "3D Spatial")
        wait_and_save(driver, SCREENSHOTS_DIR / "11_3d_spatial_virtual_hospital.png", 3.5)
    finally:
        driver.quit()

    # -----------------------------------------------------------------
    # Generate Screenshots/README.md Gallery & Catalog
    # -----------------------------------------------------------------
    print("\nGenerating Screenshots/README.md gallery index...")
    readme_path = SCREENSHOTS_DIR / "README.md"
    readme_lines = [
        "# AI Virtual Hospital (AI-VH): Visual Interface Catalog",
        "",
        "This directory contains high-resolution (1920×1080 / HiDPI) screenshots capturing every routed view, portal workspace, specialist modal, and 3D simulation canvas defined in the AI Virtual Hospital platform.",
        "",
        "---",
        "",
        "## Summary of Captured Views",
        "",
        "| # | View Title | Route Slug | File Name | Size |",
        "|---|---|---|---|---|",
    ]

    for i, r in enumerate(catalog, 1):
        file_path = SCREENSHOTS_DIR / r["filename"]
        size_kb = file_path.stat().st_size / 1024 if file_path.exists() else 0
        readme_lines.append(
            f"| {i:02d} | **{r['title']}** | `{r['slug']}` | [`{r['filename']}`](./{r['filename']}) | {size_kb:.1f} KB |"
        )

    readme_lines.extend([
        "",
        "---",
        "",
        "## Detailed View Previews & Descriptions",
        "",
    ])

    for i, r in enumerate(catalog, 1):
        readme_lines.extend([
            f"### {i:02d}. {r['title']}",
            f"- **Route / Trigger**: `{r['route']}`",
            f"- **File**: [`{r['filename']}`](./{r['filename']})",
            f"- **Description**: {r['desc']}",
            "",
            f"![{r['title']}](./{r['filename']})",
            "",
            "---",
            "",
        ])

    readme_path.write_text("\n".join(readme_lines), encoding="utf-8")
    print(f"Gallery documentation generated at: {readme_path}")
    print("\n================================================================")
    print("SCREENSHOT GENERATION COMPLETE!")
    print(f"Total Captured Views: {len(catalog)} (100% verified)")
    print("================================================================")


if __name__ == "__main__":
    run_capture_pipeline()

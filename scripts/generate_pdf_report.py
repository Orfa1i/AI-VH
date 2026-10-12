"""
AI-VH Functional Architecture PDF Generator
Reads docs/report_template.html and compiles it to AI-VH_Functional_Architecture_Report.pdf using headless Chrome.
"""

import os
import subprocess
import sys

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    template_path = os.path.join(root_dir, "docs", "report_template.html")
    output_pdf = os.path.join(root_dir, "AI-VH_Functional_Architecture_Report.pdf")

    if not os.path.exists(template_path):
        print(f"ERROR: Template file not found at {template_path}")
        sys.exit(1)

    chrome_candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]

    browser_bin = None
    for cand in chrome_candidates:
        if os.path.exists(cand):
            browser_bin = cand
            break

    if not browser_bin:
        print("ERROR: Neither Google Chrome nor Microsoft Edge was found.")
        sys.exit(1)

    print(f"Rendering PDF with {os.path.basename(browser_bin)}...")
    print(f"Input: {template_path}")
    print(f"Output: {output_pdf}")

    cmd = [
        browser_bin,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={output_pdf}",
        template_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR rendering PDF: {result.stderr}")
        sys.exit(result.returncode)

    if not os.path.exists(output_pdf):
        print(f"ERROR: PDF file not found at {output_pdf}")
        sys.exit(1)

    file_size_kb = os.path.getsize(output_pdf) / 1024
    print(f"SUCCESS: Generated PDF at {output_pdf}")
    print(f"File size: {file_size_kb:.1f} KB")

if __name__ == "__main__":
    main()

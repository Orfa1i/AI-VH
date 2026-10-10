# -*- coding: utf-8 -*-
"""
Assembler for frontend/public/case-room.html
Combines CSS, HTML markup, reference compact SVGs with animation hooks,
clinical cases, and deliberation engine.
"""

import os
import json
import subprocess
from gen_css import CSS_CONTENT
from gen_html import get_html_markup
from gen_cases import CASES_CODE
from gen_engine import ENGINE_CODE

SVG_DIR = r"C:\Users\PCD\Desktop\AI-VH\agent-animation-restore\reference\svg"
MAPPING = {
    'ob': 'vh-agent-obstetrics-compact.svg',
    'gy': 'vh-agent-gynecology-compact.svg',
    'em': 'vh-agent-emergency-compact.svg',
    'im': 'vh-agent-internal-medicine-compact.svg',
    'ca': 'vh-agent-cardiology-compact.svg',
    'ne': 'vh-agent-neurology-compact.svg',
    'su': 'vh-agent-surgery-compact.svg',
}

def main():
    print("Reading thumbnail assets from git HEAD~1...")
    proc = subprocess.run(['git', 'show', 'HEAD~1:frontend/public/case-room.html'], capture_output=True, text=True, encoding='utf-8')
    orig = proc.stdout

    av_idx = orig.find('const AV = {')
    avsvg_idx = orig.find('const AVSVG = {')
    if av_idx == -1 or avsvg_idx == -1:
        raise ValueError(f"Could not locate AV: av_idx={av_idx}")
    av_block = orig[av_idx:avsvg_idx].strip()

    # Load pristine reference compact SVGs
    avsvg_dict = {}
    for key, filename in MAPPING.items():
        filepath = os.path.join(SVG_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            avsvg_dict[key] = f.read().strip()
    avsvg_block = f"const AVSVG = {json.dumps(avsvg_dict)};"

    # Logo
    logo_idx = orig.find('data:image/svg+xml;base64,')
    logo_end = orig.find('"', logo_idx)
    logo_src = orig[logo_idx:logo_end]

    print(f"Extracted: AV ({len(av_block)} chars), AVSVG ({len(avsvg_block)} chars), Logo ({len(logo_src)} chars)")

    # Generate HTML base
    html = get_html_markup(logo_src)

    # Inject CSS
    html = html.replace('/* CSS will be injected here */', CSS_CONTENT)

    # Combine script content
    script_content = f"""
{av_block}

{avsvg_block}

{CASES_CODE}

{ENGINE_CODE}
"""

    # Inject script
    html = html.replace('// Logic injected here', script_content)

    print(f"Assembled final HTML. Total length: {len(html)} chars, {len(html.splitlines())} lines.")

    # Write out to frontend/public/case-room.html
    out_path = r'C:\Users\PCD\Desktop\AI-VH\frontend\public\case-room.html'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print("Successfully wrote frontend/public/case-room.html!")

if __name__ == '__main__':
    main()

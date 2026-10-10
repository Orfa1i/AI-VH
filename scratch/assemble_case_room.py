# -*- coding: utf-8 -*-
"""
Assembler for frontend/public/case-room.html
Combines CSS, HTML markup, pristine extracted SVGs/avatars/logo, clinical cases, and deliberation engine.
"""

import os
import subprocess
from gen_css import CSS_CONTENT
from gen_html import get_html_markup
from gen_cases import CASES_CODE
from gen_engine import ENGINE_CODE

def main():
    print("Reading pristine assets from git HEAD~1...")
    proc = subprocess.run(['git', 'show', 'HEAD~1:frontend/public/case-room.html'], capture_output=True, text=True, encoding='utf-8')
    orig = proc.stdout

    av_idx = orig.find('const AV = {')
    avsvg_idx = orig.find('const AVSVG = {')
    cases_idx = orig.find('const CASES = {')

    if av_idx == -1 or avsvg_idx == -1 or cases_idx == -1:
        raise ValueError(f"Could not locate AV or AVSVG: av_idx={av_idx}, avsvg_idx={avsvg_idx}, cases_idx={cases_idx}")

    av_block = orig[av_idx:avsvg_idx].strip()
    avsvg_block = orig[avsvg_idx:cases_idx].strip()

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
    with open('frontend/public/case-room.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Successfully wrote frontend/public/case-room.html!")

if __name__ == '__main__':
    main()

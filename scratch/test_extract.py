# -*- coding: utf-8 -*-
"""
Generator script for frontend/public/case-room.html
Assembles the complete Asklevia Trajectory Graph page with:
1. No percentages or '6 of 7' in header.
2. Obstetrics renamed to Infectious Disease (id), Gynecology (gy) verified.
3. Left Clinical Dossier sidebar with case selector, vitals, labs, imaging thumbnails, modal.
4. Real MedGemma router integration via POST /api/router/route.
5. Fish Audio TTS API integration with browser SpeechSynthesis fallback and concise voice lines.
6. Multi-specialist referral animated sequence with consensus agreement scoring.
"""

import json
import os
import re

with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    orig = f.read()

# 1. Extract AV and AVSVG
av_idx = orig.find('const AV = {')
avsvg_idx = orig.find('const AVSVG = {')
dollar_idx = orig.find('const $ = s =>')

if av_idx == -1 or avsvg_idx == -1 or dollar_idx == -1:
    raise ValueError(f"Could not locate AV or AVSVG: av_idx={av_idx}, avsvg_idx={avsvg_idx}, dollar_idx={dollar_idx}")

av_block = orig[av_idx:avsvg_idx].strip()
avsvg_block = orig[avsvg_idx:dollar_idx].strip()

# 2. Extract Asklevia Symbol base64 logo
logo_match = re.search(r'<div class="rh"><img src="([^"]+)"', orig)
logo_src = logo_match.group(1) if logo_match else ""

print("Extracted AV block length:", len(av_block))
print("Extracted AVSVG block length:", len(avsvg_block))
print("Extracted logo src length:", len(logo_src))

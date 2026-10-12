# -*- coding: utf-8 -*-
"""
Builder for frontend/public/case-room.html
"""
import json
import re

with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    orig = f.read()

# 1. Extract AV and AVSVG
av_idx = orig.find('const AV = {')
avsvg_idx = orig.find('const AVSVG = {')
dollar_idx = orig.find('const $ = s =>')

av_block = orig[av_idx:avsvg_idx].strip()
avsvg_block = orig[avsvg_idx:dollar_idx].strip()

# 2. Extract Asklevia Logo
logo_match = re.search(r'<div class="rh"><img src="([^"]+)"', orig)
logo_src = logo_match.group(1) if logo_match else ""

print("Assets ready. AV len:", len(av_block), "AVSVG len:", len(avsvg_block))

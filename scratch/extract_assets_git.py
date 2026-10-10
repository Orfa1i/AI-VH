# -*- coding: utf-8 -*-
import subprocess
import re

proc = subprocess.run(['git', 'show', 'HEAD~1:frontend/public/case-room.html'], capture_output=True, text=True, encoding='utf-8')
orig = proc.stdout
print("Original length from git HEAD~1:", len(orig))

av_idx = orig.find('const AV = {')
avsvg_idx = orig.find('const AVSVG = {')
dollar_idx = orig.find('const $ = s =>')

av_block = orig[av_idx:avsvg_idx].strip()
avsvg_block = orig[avsvg_idx:dollar_idx].strip()

# Find logo
logo_idx = orig.find('data:image/svg+xml;base64,')
logo_end = orig.find('"', logo_idx)
logo_src = orig[logo_idx:logo_end]

print("Extracted AV len:", len(av_block))
print("Extracted AVSVG len:", len(avsvg_block))
print("Extracted logo len:", len(logo_src))

# Save logo to a file so it's always preserved
with open('scratch/logo_src.txt', 'w', encoding='utf-8') as f:
    f.write(logo_src)

print("Saved logo to scratch/logo_src.txt")

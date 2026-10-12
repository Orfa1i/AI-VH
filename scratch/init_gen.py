import json

with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    orig = f.read()

av_idx = orig.find('const AV = {')
avsvg_idx = orig.find('const AVSVG = {')
dollar_idx = orig.find('const $ = s =>')

av_str = orig[av_idx:avsvg_idx].strip()
avsvg_str = orig[avsvg_idx:dollar_idx].strip()

# Now create generate_case_room.py
with open('scratch/generate_case_room.py', 'w', encoding='utf-8') as f:
    f.write(f'''# -*- coding: utf-8 -*-
import json

with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f_orig:
    orig = f_orig.read()

av_idx = orig.find('const AV = {{')
avsvg_idx = orig.find('const AVSVG = {{')
dollar_idx = orig.find('const $ = s =>')

av_str = orig[av_idx:avsvg_idx].strip()
avsvg_str = orig[avsvg_idx:dollar_idx].strip()

# Generate the full html
''')

print("Created scratch/generate_case_room.py template")

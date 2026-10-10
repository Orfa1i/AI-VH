# -*- coding: utf-8 -*-
import subprocess

proc = subprocess.run(['git', 'show', 'HEAD~1:frontend/public/case-room.html'], capture_output=True, text=True, encoding='utf-8')
orig = proc.stdout

av_idx = orig.find('const AV = {')
avsvg_idx = orig.find('const AVSVG = {')
dollar_idx = orig.find('const $ = s =>')

av_block = orig[av_idx:avsvg_idx].strip()
avsvg_block = orig[avsvg_idx:dollar_idx].strip()

from gen_cases import CASES_CODE
from gen_engine import ENGINE_CODE

with open('scratch/part1.js', 'w', encoding='utf-8') as f:
    f.write(av_block)

with open('scratch/part2.js', 'w', encoding='utf-8') as f:
    f.write(av_block + '\n\n' + avsvg_block)

with open('scratch/part3.js', 'w', encoding='utf-8') as f:
    f.write(av_block + '\n\n' + avsvg_block + '\n\n' + CASES_CODE)

with open('scratch/part4.js', 'w', encoding='utf-8') as f:
    f.write(av_block + '\n\n' + avsvg_block + '\n\n' + CASES_CODE + '\n\n' + ENGINE_CODE)

print("Wrote parts 1 to 4.")

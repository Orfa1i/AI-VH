# -*- coding: utf-8 -*-
with open('scratch/js_logic.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
# Print every 20th line or section headers
for i, l in enumerate(lines):
    if '/*' in l or 'function' in l or 'const ' in l or 'let ' in l:
        if any(w in l for w in ['render', 'stepTo', 'tick', 'play', 'reset', 'gaze', 'layout', 'packet', 'setBoard', 'syncPlay']):
            print(f"Line {i+1}: {l.strip()[:80]}")

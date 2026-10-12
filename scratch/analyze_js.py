# -*- coding: utf-8 -*-
with open('scratch/js_logic.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
funcs = re.findall(r'(?:const|let|function)\s+([a-zA-Z0-9_$]+)\s*=', text)
print("Declared variables/functions:", funcs[:30])
print(f"Total lines in js_logic.js: {len(text.splitlines())}")

# -*- coding: utf-8 -*-
with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Find rcols
m = re.search(r'<div class=[\'"]rcols[\'"]', text)
if m:
    pos = m.start()
    print("Found rcols at:", pos)
    print(text[pos:pos+2500])
else:
    print("rcols not found by regex")

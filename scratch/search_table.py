# -*- coding: utf-8 -*-
with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'\bTABLE\b', text)]
print('Matches for TABLE:', len(matches))
for idx in matches:
    print(f'Index {idx}:')
    print(text[max(0, idx-100):min(len(text), idx+300)])
    print('='*50)

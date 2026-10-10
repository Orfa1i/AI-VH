# -*- coding: utf-8 -*-
import sys
with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'\bTABLE\b', text)]
print('Matches for TABLE:', len(matches))
for idx in matches:
    print(f'Index {idx}:')
    snippet = text[max(0, idx-80):min(len(text), idx+200)]
    sys.stdout.buffer.write(snippet.encode('utf-8', errors='replace') + b'\n' + b'='*50 + b'\n')

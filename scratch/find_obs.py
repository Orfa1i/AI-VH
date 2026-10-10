with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("Occurrences of 'Obstetrics':", len(re.findall(r'Obstetrics', text, re.IGNORECASE)))
for m in re.finditer(r'Obstetrics', text, re.IGNORECASE):
    start = max(0, m.start() - 40)
    end = min(len(text), m.end() + 40)
    print("...", text[start:end].replace('\n', ' '), "...")

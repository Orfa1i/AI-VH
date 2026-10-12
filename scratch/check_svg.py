import json, re

with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'const AVSVG = (\{.+?\});', text, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    print("ob svg length:", len(data.get('ob', '')))
    print("gy svg length:", len(data.get('gy', '')))

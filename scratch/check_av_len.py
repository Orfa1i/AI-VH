with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
av_match = re.search(r'const AV = ({.*?});', text, re.DOTALL)
if av_match:
    print("Found AV, length:", len(av_match.group(1)))

svg_match = re.search(r'const AVSVG = ({.*?});', text, re.DOTALL)
if svg_match:
    print("Found AVSVG, length:", len(svg_match.group(1)))

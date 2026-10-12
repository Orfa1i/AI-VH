import os
import re

files = []
for root, dirs, filenames in os.walk('frontend/src'):
    if any(ignore in root for ignore in ['node_modules', '.git', 'dist', '__tests__']):
        continue
    for f in filenames:
        if f.endswith('.tsx') or f.endswith('.ts'):
            files.append(os.path.join(root, f))

found = []
for f in files:
    with open(f, 'r', encoding='utf-8') as fp:
        lines = fp.readlines()
    for idx, line in enumerate(lines):
        clean_line = line.strip()
        # look for any ! that is part of text or string
        # ignore typescript negation, !=, !==, !empty, etc.
        m = re.findall(r'[a-zA-Z0-9\s\.\,\?]+!', line)
        for match in m:
            clean = match.strip()
            if len(clean) > 2 and not clean.startswith('//') and not clean.startswith('/*'):
                # filter out ts expressions like foo! or bar.baz!
                if not re.match(r'^[a-zA-Z0-9_]+\!$', clean):
                    found.append((f, idx + 1, clean, clean_line))

print(f"Total potential ! found: {len(found)}")
for item in found:
    print(f"  {item[0]}:{item[1]} -> '{item[2]}' in: {item[3]}")

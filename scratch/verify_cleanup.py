# -*- coding: utf-8 -*-
with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
checks = [
    r'6 of 7 specialists assigned',
    r'<small>%</small>',
    r'class=[\'"]v[\'"]',
    r'class=[\'"]rbar[\'"]',
    r'AG\[k\]\.rel',
]
for p in checks:
    matches = list(re.finditer(p, text))
    print(f'Pattern {p:<30}: {len(matches)} matches')

# Also verify new agent names
print("Infectious Disease in text:", text.count("Infectious Disease"))
print("Obstetrics in text:", text.count("Obstetrics"))
print("Gynecology in text:", text.count("Gynecology"))
print("Dr. Anthony Mercer in text:", text.count("Dr. Anthony Mercer"))
print("Dr. Evelyn Reed in text:", text.count("Dr. Evelyn Reed"))
print("Harrison's Infectious Diseases in text:", text.count("Harrison's Infectious Diseases"))
print("Williams Gynecology in text:", text.count("Williams Gynecology"))

with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("header:", text.find('<header'))
print("class='top':", text.find('class="top"'))
print("class='pt':", text.find('class="pt"'))
print("first 300 chars of body:", text[text.find('<body>'):text.find('<body>')+300])

# -*- coding: utf-8 -*-
with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('id="rcols"')
print(text[pos-800:pos+100])

# -*- coding: utf-8 -*-
with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('const AG =')
print(text[pos:pos+1500])

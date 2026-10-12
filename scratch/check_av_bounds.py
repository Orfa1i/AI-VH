with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
av_start = text.find('const AV = {')
avsvg_start = text.find('const AVSVG = {')
dollar_start = text.find('const $ = s =>')

print("av_start:", av_start)
print("avsvg_start:", avsvg_start)
print("dollar_start:", dollar_start)
print("text between avsvg and dollar:", text[avsvg_start+len('const AVSVG = {'):dollar_start][:200])

# Let's check how AV and AVSVG are declared in the original case-room.html
with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    orig = f.read()

av_idx = orig.find('const AV = {')
avsvg_idx = orig.find('const AVSVG = {')
dollar_idx = orig.find('const $ = s =>')

av_str = orig[av_idx:avsvg_idx].strip()
avsvg_str = orig[avsvg_idx:dollar_idx].strip()

print("AV starts with:", av_str[:50])
print("AV ends with:", av_str[-50:])
print("AVSVG starts with:", avsvg_str[:50])
print("AVSVG ends with:", avsvg_str[-50:])

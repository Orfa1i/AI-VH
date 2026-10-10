with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

dollar_start = text.find('const $ = s =>')
with open('scratch/js_logic.js', 'w', encoding='utf-8') as f_out:
    f_out.write(text[dollar_start:])
print("Wrote js_logic.js, length:", len(text[dollar_start:]))

with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find out how many lines and the positions of major components
print("Total chars:", len(text))
head_end = text.find('</head>')
print("Head end at:", head_end)
style_start = text.find('<style>')
style_end = text.find('</style>')
print("Style from", style_start, "to", style_end)
script_start = text.find('<script>')
script_end = text.find('</script>')
print("Script from", script_start, "to", script_end)

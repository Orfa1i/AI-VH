with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    text = f.read()

part1 = text[:text.find('const AV = {')]
part2 = text[text.find('const $ = s =>'):]

print("Part 1 length (HTML + CSS up to AV):", len(part1))
print("Part 2 length (JS after AVSVG):", len(part2))

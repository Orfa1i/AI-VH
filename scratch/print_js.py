with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if i < 345:
        continue
    if 'data:image/svg' in l:
        print(f"Line {i+1}: [SVG DATA URI TRUNCATED]")
    else:
        print(f"Line {i+1}: {l[:100]}", end='')
        if not l.endswith('\n'):
            print()

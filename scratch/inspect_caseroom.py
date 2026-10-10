with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for i, line in enumerate(lines):
    l = line.strip()
    tags = ['<style', '</style', '<body', '<header', '<script', '</script', 'class="router', 'class="room', 'class="draft', 'const AG =', 'const TABLE =']
    for t in tags:
        if t in l:
            print(f"Line {i+1}: {l[:90]}")

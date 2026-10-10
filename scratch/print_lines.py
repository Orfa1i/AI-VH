with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 345 <= i <= 445:
        # truncate long lines
        if len(l) > 150:
            print(f"L{i+1}: {l[:150]}... [len={len(l)}]")
        else:
            print(f"L{i+1}: {l.strip()}")

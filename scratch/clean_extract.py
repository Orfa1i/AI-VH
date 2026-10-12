with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('scratch/case-room-clean.txt', 'w', encoding='utf-8') as out:
    for i, l in enumerate(lines):
        if 'data:image/svg' in l:
            # find key if any
            out.write(f"/* Line {i+1}: SVG DATA OMITTED */\n")
        else:
            out.write(f"/* L{i+1} */ {l}")
print("Done writing clean file.")

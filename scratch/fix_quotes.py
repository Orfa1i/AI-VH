# -*- coding: utf-8 -*-
with open('scratch/gen_cases.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    stripped = line.strip()
    if stripped.startswith("detail: '") and stripped.endswith("',"):
        val = stripped[9:-2]
        val = val.replace("\\'", "'")
        val = val.replace('"', '\\"')
        prefix = line[:line.find('detail:')]
        new_lines.append(f'{prefix}detail: "{val}",\n')
    elif stripped.startswith("voice: '") and stripped.endswith("',"):
        val = stripped[8:-2]
        val = val.replace("\\'", "'")
        val = val.replace('"', '\\"')
        prefix = line[:line.find('voice:')]
        new_lines.append(f'{prefix}voice: "{val}",\n')
    elif stripped.startswith("short: '") and stripped.endswith("',"):
        val = stripped[8:-2]
        val = val.replace("\\'", "'")
        val = val.replace('"', '\\"')
        prefix = line[:line.find('short:')]
        new_lines.append(f'{prefix}short: "{val}",\n')
    else:
        new_lines.append(line)

with open('scratch/gen_cases.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Updated scratch/gen_cases.py")

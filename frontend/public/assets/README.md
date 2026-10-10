# Virtual Hospital AI agent avatars

Seven specialist agents. They share one face, coat, headset and material. Each specialty has its own colour, chest badge and signature detail.

| Agent | Colour | Badge | Signature detail | Reference |
|---|---|---|---|---|
| Internal Medicine | Indigo #2B2FD9 | Capsule cross | Clean clinical display | Harrison's |
| Cardiology | Blue #1F7BEA | Heart and trace | Live trace on the face display | Braunwald's |
| Neurology | Violet #5B3DF5 | Brain | Linked nodes on the face display | Adams and Victor's |
| Surgery | Verdant #13A06B | Scalpel at 23° | Surgical cap | Schwartz's |
| Emergency Medicine | Teal #0E9AA7 | Stopwatch and cross | Headlamp | Tintinalli's |
| Obstetrics | Sky #2E9FE6 | Pregnant figure | Headband with heart | Williams Obstetrics |
| Gynecology | Jade #0FA88A | Venus symbol | Flower clip | Williams Gynecology |

## Files

- `svg/`: the master artwork for each agent, in four versions:
  - `-circle`: the default.
  - `-rounded`: a rounded square for app tiles and cards.
  - `-transparent`: the character only, for coloured or patterned surfaces.
  - `-compact`: a face crop for small sizes.
- `png/`:
  - `vh-agent-<specialty>-<size>.png`: the circle version at 1024, 512, 256, 128 and 64px.
  - `-rounded-1024` and `-transparent-1024`: the rounded and character-only versions at 1024px.
  - `-compact-<size>`: the face crop at 1024, 128, 64, 48 and 32px.
- `vh-agents-overview.png`: the whole set on one sheet.
- `generator-av.py`: the script that builds the SVGs. Edit a colour or detail there to regenerate all the files consistently.

## Use

- **Size:** use the circle version at 72px and above. Below 72px (chat bubbles, lists, notifications), switch to `-compact`.
- **Labelling:** always show the agent's name with "AI agent" next to the avatar. These are AI agents, not people. Pair them with the line about physicians reviewing every report.
- **Background:** keep the avatars on Paper (#F7F8FB) or white, in line with the light-mode brand rule.

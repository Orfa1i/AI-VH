"""Virtual Hospital AI doctor agents: a unified avatar set (1024 grid, circle-safe).
One body, one face, one material; each specialty owns a colour, a chest badge glyph and one signature detail."""
import math

INK = "#0F1222"; PAPER = "#F7F8FB"; GRAPHITE = "#4A5068"

AGENTS = [
    # key, name, book, colour, light tint, deep shade
    ("internal-medicine", "Internal Medicine", "Harrison's", "#2B2FD9"),
    ("cardiology", "Cardiology", "Braunwald's", "#1F7BEA"),
    ("neurology", "Neurology", "Adams and Victor's", "#5B3DF5"),
    ("surgery", "Surgery", "Schwartz's", "#13A06B"),
    ("emergency", "Emergency Medicine", "Tintinalli's", "#0E9AA7"),
    ("obstetrics", "Obstetrics", "Williams Obstetrics", "#2E9FE6"),
    ("gynecology", "Gynecology", "Williams Gynecology", "#0FA88A"),
]

def hx(c): c = c.lstrip("#"); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
def mix(a, b, t):
    A, B = hx(a), hx(b); return "#%02X%02X%02X" % tuple(round(A[i] + (B[i] - A[i]) * t) for i in range(3))

# ---- specialty glyphs on a 120 box centred at 0,0, stroked in the agent colour
def glyph(key, c, w=12):
    s = f'fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"'
    if key == "internal-medicine":   # the Virtual Hospital cross, built from two capsules
        return f'<path d="M0 -40 V40 M-40 0 H40" {s} stroke-width="{w*1.9}"/>'
    if key == "cardiology":
        return (f'<path d="M0 34 C-50 4 -50 -40 -22 -40 C-10 -40 -2 -32 0 -24 C2 -32 10 -40 22 -40 C50 -40 50 4 0 34Z" {s}/>'
                f'<path d="M-48 -2 H-20 L-10 -20 L4 16 L14 -2 H48" {s} stroke-width="{w*.8}"/>')
    if key == "neurology":           # a brain: two hemispheres, a midline and one fold each side
        return (f'<path d="M0 -40 C-20 -50 -46 -38 -44 -16 C-58 -6 -54 18 -40 22 C-42 42 -16 48 0 38 Z" {s}/>'
                f'<path d="M0 -40 C20 -50 46 -38 44 -16 C58 -6 54 18 40 22 C42 42 16 48 0 38 Z" {s}/>'
                f'<path d="M-24 -22 C-12 -18 -12 -4 -24 2 M24 -22 C12 -18 12 -4 24 2 M-26 22 C-18 18 -10 22 -8 28 M26 22 C18 18 10 22 8 28" {s} stroke-width="{w*.7}"/>')
    if key == "surgery":             # scalpel at the brand's 23 degrees
        return (f'<g transform="rotate(-23) translate(-4 0)"><rect x="-60" y="-9" width="64" height="18" rx="9" fill="{c}"/>'
                f'<path d="M8 -12 L50 -12 C64 -12 70 -4 66 4 C54 15 30 15 8 12 Z" fill="{c}"/></g>')
    if key == "emergency":           # stopwatch with a cross: time-critical care
        return (f'<circle cx="0" cy="8" r="38" {s}/><path d="M0 -38 V-46 M-12 -48 H12 M30 -24 L38 -32" {s}/>'
                f'<path d="M0 -8 V24 M-16 8 H16" {s} stroke-width="{w*.95}"/>')
    if key == "obstetrics":          # mother and child: an arc cradling a small circle
        return (f'<circle cx="-4" cy="-42" r="13" fill="{c}"/>'
                f'<path d="M-12 -24 H6 C10 -14 8 -6 12 -2 C40 6 40 40 12 44 L12 52 H-14 C-20 26 -22 0 -12 -24 Z" fill="{c}"/>')
    if key == "gynecology":          # Venus symbol
        return f'<circle cx="0" cy="-12" r="28" {s}/><path d="M0 16 V50 M-17 34 H17" {s}/>'
    return ""

def avatar(key, name, book, c, *, frame="circle", bg=True, uid="", compact=False):
    u = uid or key
    tint = mix(c, "#FFFFFF", .86); tint2 = mix(c, "#FFFFFF", .70); deep = mix(c, INK, .35); light = mix(c, "#FFFFFF", .45)
    o = []
    o.append(f'''<defs>
  <radialGradient id="bg{u}" cx="50%" cy="38%" r="70%"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".55" stop-color="{tint}"/><stop offset="1" stop-color="{tint2}"/></radialGradient>
  <pattern id="dots{u}" width="40" height="40" patternUnits="userSpaceOnUse"><circle cx="20" cy="20" r="2.4" fill="{c}" opacity=".22"/></pattern>
  <radialGradient id="fade{u}" cx="50%" cy="42%" r="60%"><stop offset=".45" stop-color="#000"/><stop offset="1" stop-color="#fff"/></radialGradient>
  <mask id="dm{u}"><rect width="1024" height="1024" fill="url(#fade{u})"/></mask>
  <linearGradient id="head{u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#E4E9F2"/></linearGradient>
  <linearGradient id="face{u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FBFCFE"/><stop offset="1" stop-color="{mix(c, '#FFFFFF', .9)}"/></linearGradient>
  <linearGradient id="coat{u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#E7EBF3"/></linearGradient>
  <linearGradient id="pod{u}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{light}"/><stop offset="1" stop-color="{c}"/></linearGradient>
  <linearGradient id="scrub{u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c}"/><stop offset="1" stop-color="{deep}"/></linearGradient>
  <filter id="sh{u}" x="-30%" y="-30%" width="160%" height="170%"><feDropShadow dx="0" dy="22" stdDeviation="24" flood-color="{mix(c, INK, .6)}" flood-opacity=".16"/></filter>
  <filter id="sh2{u}" x="-30%" y="-30%" width="160%" height="170%"><feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="{INK}" flood-opacity=".12"/></filter>
  <clipPath id="clip{u}">{'<circle cx="512" cy="512" r="512"/>' if frame == 'circle' else '<rect width="1024" height="1024" rx="232"/>'}</clipPath>
</defs>''')
    o.append(f'<g clip-path="url(#clip{u})">')
    if bg:
        o.append(f'<rect width="1024" height="1024" fill="url(#bg{u})"/><rect width="1024" height="1024" fill="url(#dots{u})" mask="url(#dm{u})"/>')
        # level band behind the head: the Virtual Hospital cross's horizontal stroke, as an aura
        o.append(f'<circle cx="512" cy="455" r="330" fill="none" stroke="{c}" stroke-opacity=".10" stroke-width="2"/>')
        o.append(f'<circle cx="512" cy="455" r="270" fill="#FFFFFF" fill-opacity=".55"/>')
    # ---- character, scaled into the circle-safe area
    o.append(f'<g transform="{"translate(-256 -236) scale(1.5)" if compact else "translate(31 6) scale(.94)"}">')
    # ---- body: white coat over scrubs
    o.append(f'<g filter="url(#sh{u})">')
    o.append(f'<path d="M150 1220 C150 880 270 792 512 792 C754 792 874 880 874 1220 Z" fill="url(#coat{u})"/>')
    o.append(f'<path d="M426 796 L512 930 L598 796 Z" fill="url(#scrub{u})"/>')
    o.append('</g>')
    # lapels
    o.append(f'<path d="M426 796 L512 930 L470 1220 L370 1220 C380 1000 402 880 426 796Z" fill="#FFFFFF"/>')
    o.append(f'<path d="M598 796 L512 930 L554 1220 L654 1220 C644 1000 622 880 598 796Z" fill="#F4F6FA"/>')
    o.append(f'<path d="M426 796 L512 930 L598 796" fill="none" stroke="#D9DEE8" stroke-width="3"/>')
    o.append(f'<path d="M512 930 L512 1220" stroke="#D9DEE8" stroke-width="3"/>')
    # neck
    o.append(f'<rect x="458" y="700" width="108" height="120" rx="40" fill="#DCE2EC"/>')
    o.append(f'<rect x="458" y="760" width="108" height="16" fill="#CDD4E1" opacity=".7"/>')
    # stethoscope: tubing around the neck, one drop to a chestpiece on the left of the chest
    tube = "#2A3049"
    o.append(f'<path d="M444 790 C430 880 470 920 512 920 C554 920 594 880 580 790" fill="none" stroke="{tube}" stroke-width="13" stroke-linecap="round"/>')
    o.append(f'<path d="M466 906 C436 930 404 936 388 960" fill="none" stroke="{tube}" stroke-width="13" stroke-linecap="round"/>')
    o.append(f'<circle cx="382" cy="976" r="32" fill="#EEF1F6" stroke="{tube}" stroke-width="10"/><circle cx="382" cy="976" r="15" fill="{c}"/>')
    # chest badge with the specialty glyph
    o.append(f'<g filter="url(#sh2{u})"><circle cx="672" cy="904" r="72" fill="#FFFFFF"/></g>')
    o.append(f'<circle cx="672" cy="904" r="72" fill="none" stroke="{tint2}" stroke-width="3"/>')
    o.append(f'<g transform="translate(672 904) scale(.82)">{glyph(key, c)}</g>')
    # ---- head (sits low on a short neck, with a stand collar from the coat)
    o.append(f'<path d="M430 800 C440 760 470 744 512 744 C554 744 584 760 594 800 L578 812 C560 790 540 782 512 782 C484 782 464 790 446 812 Z" fill="#FFFFFF" stroke="#D9DEE8" stroke-width="3"/>')
    o.append('<g transform="translate(0 34)">')
    # ear pods (the agent's headset) in the specialty colour
    o.append(f'<rect x="276" y="402" width="64" height="150" rx="32" fill="url(#pod{u})"/>')
    o.append(f'<rect x="684" y="402" width="64" height="150" rx="32" fill="url(#pod{u})"/>')
    o.append(f'<g filter="url(#sh{u})"><rect x="306" y="250" width="412" height="460" rx="190" fill="url(#head{u})"/></g>')
    o.append(f'<rect x="306" y="250" width="412" height="460" rx="190" fill="none" stroke="#FFFFFF" stroke-width="4" opacity=".9"/>')
    # face display
    o.append(f'<rect x="354" y="352" width="316" height="264" rx="124" fill="url(#face{u})" stroke="{tint2}" stroke-width="3"/>')
    o.append(f'<path d="M392 420 C400 386 430 364 470 360" fill="none" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round" opacity=".9"/>')
    # eyes: level capsules with a highlight; smile in the agent colour; soft cheeks
    for ex in (452, 572):
        o.append(f'<rect x="{ex-21}" y="430" width="42" height="72" rx="21" fill="{INK}"/>')
        o.append(f'<circle cx="{ex+6}" cy="451" r="8" fill="#FFFFFF" opacity=".95"/>')
    o.append(f'<circle cx="406" cy="536" r="22" fill="{c}" opacity=".16"/><circle cx="618" cy="536" r="22" fill="{c}" opacity=".16"/>')
    o.append(f'<path d="M474 540 Q512 572 550 540" fill="none" stroke="{c}" stroke-width="14" stroke-linecap="round"/>')
    # head-top status light: every agent is visibly a live system
    o.append(f'<rect x="478" y="282" width="68" height="16" rx="8" fill="{c}" opacity=".9"/>')
    # ---- signature detail per specialty
    if key == "surgery":             # surgical cap over the crown
        o.append(f'<path d="M318 400 C318 268 420 228 512 228 C604 228 706 268 706 400 C640 376 384 376 318 400 Z" fill="url(#scrub{u})"/>')
        o.append(f'<path d="M330 392 C420 368 604 368 694 392" fill="none" stroke="#FFFFFF" stroke-opacity=".35" stroke-width="4"/>')
        for i, x in enumerate(range(372, 680, 46)):
            o.append(f'<circle cx="{x}" cy="{318 + abs(512-x)*0.12}" r="5" fill="#FFFFFF" opacity=".28"/>')
    if key == "emergency":           # headlamp on a band
        o.append(f'<path d="M310 360 C400 320 624 320 714 360" fill="none" stroke="{deep}" stroke-width="22" stroke-linecap="round"/>')
        o.append(f'<circle cx="512" cy="318" r="40" fill="#FFFFFF" stroke="{deep}" stroke-width="12"/><circle cx="512" cy="318" r="18" fill="{c}"/>')
        o.append(f'<circle cx="512" cy="318" r="80" fill="{c}" opacity=".10"/>')
    if key == "cardiology":          # a live trace across the forehead of the display
        o.append(f'<path d="M420 392 H476 L490 372 L508 414 L524 384 L534 392 H604" fill="none" stroke="{c}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>')
    if key == "neurology":           # three linked nodes on the forehead
        o.append(f'<path d="M462 396 L512 378 L562 396" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round"/>')
        for x, y in ((462, 396), (512, 378), (562, 396)):
            o.append(f'<circle cx="{x}" cy="{y}" r="10" fill="{c}"/>')
    if key == "obstetrics":          # a soft headband with a small heart
        o.append(f'<path d="M316 372 C400 320 624 320 708 372" fill="none" stroke="{light}" stroke-width="20" stroke-linecap="round"/>')
        o.append(f'<path d="M512 352 C488 336 482 312 498 306 C506 303 511 308 512 312 C513 308 518 303 526 306 C542 312 536 336 512 352Z" fill="{c}"/>')
    if key == "gynecology":          # a single flower clip on the side of the head
        cx, cy = 660, 318
        for k in range(5):
            a = k / 5 * 2 * math.pi - math.pi / 2
            o.append(f'<circle cx="{cx + 20*math.cos(a):.1f}" cy="{cy + 20*math.sin(a):.1f}" r="16" fill="{light}"/>')
        o.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="{c}"/>')
    o.append('</g></g></g>')
    if frame == "circle" and bg:
        o.append(f'<circle cx="512" cy="512" r="510" fill="none" stroke="{tint2}" stroke-width="4"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">{"".join(o)}</svg>'

# Virtual Hospital by Asklevia: brand kit

The symbol is the Asklevia helix with its middle band set level, so the staff and band form a medical cross. Everything else (colours, type, light-mode rule, voice) follows the Asklevia brand guide.

## Files

- `svg/`: master artwork. Use SVG wherever you can.
  - `vh-logo-horizontal`: the primary lockup, with "by Asklevia". Also in `-ink` and `-indigo` one-colour versions.
  - `vh-logo-stacked`: for square or centred layouts. Also in `-ink`.
  - `vh-logo-compact`: symbol and name without "by Asklevia", for headers and small placements.
  - `vh-symbol`: the full symbol. Also in `-ink` and `-indigo`.
  - `vh-symbol-small`: a heavier cut with no back bands, for 48px and below.
  - `vh-wordmark`: the name only.
  - `vh-app-icon`: full-bleed version, for the stores to mask.
  - `vh-app-icon-rounded`: rounded version, for web and PWA.
  - `vh-favicon`: the favicon artwork.
  - `vh-thumbnail-square`: the square thumbnail artwork.
- `png/symbol/`: transparent symbol PNGs at 64, 128, 256, 512, 1024 and 2048px, plus an ink version at 1024.
- `png/logo/`: transparent logo PNGs.
  - Horizontal lockup at 400, 800, 1600 and 3200px wide.
  - Ink and indigo versions at 1600px.
  - Stacked at 300, 600 and 1200px.
  - Compact at 800px.
- `png/app-icon/`: icons at 1024 (store master), 512, 256 and 192 (Android/PWA), 180 (`apple-touch-icon`), 167, 152 and 120.
- `png/favicon/` and `favicon.ico`: favicons at 16, 32, 48 and 64px. The .ico contains 16, 32 and 48.
- `png/social/`:
  - `vh-thumbnail-1080x1080` and `-512x512`: square thumbnails for posts, listings and directories.
  - `vh-avatar-800x800` and `-400x400`: profile pictures. The symbol sits inside the circle-crop safe area.
  - `vh-og-1200x630`: the link preview image for the website (`og:image`).
  - `vh-linkedin-cover-1128x191` and `@2x`: LinkedIn cover.
  - `vh-x-header-1500x500`: X header.
  - On the LinkedIn cover and the X header, the lockup sits on the right because the profile picture covers the lower left.

## Web setup

```html
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/vh-favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon-180.png">
<meta property="og:image" content="https://<your-domain>/vh-og-1200x630.png">
```

## Rules

- **Clear space:** keep space equal to the cap height of "Virtual" free on every side of a lockup.
- **Minimum sizes:**
  - Horizontal lockup: 160px wide, or 35mm in print.
  - Below 160px, use the compact lockup.
  - At 48px and below, use `vh-symbol-small` or the favicon.
- **Colour:** the full-colour version goes on Paper (#F7F8FB) or White only. Where colour is limited, use the ink or indigo one-colour versions.
- **Dark or photographic backgrounds:** put the logo on a white plate. The brand is light-mode only.
- **Don't:**
  - recolour, reorder or add gradients to the bands
  - tilt the level band, which is the whole idea
  - rotate the symbol or add effects
  - retype the name in another font, because the artwork is outlined Funnel Display
- **Voice:**
  - Describe the product as "AI-assisted diagnosis, reviewed by clinicians". Never say "auto-diagnosis" or "diagnosed by AI".
  - No exclamation marks, emoji or invented claims.

## Colour

Ink #0F1222 · Graphite #4A5068 · Paper #F7F8FB · Indigo #2B2FD9 · Violet #5B3DF5 · Blue #1F7BEA · Teal #0E9AA7 · Verdant #13A06B

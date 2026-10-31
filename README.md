# 3DxDor colour swatches

Public colour library for 3DxDor customers: the filaments and resins currently on the shelf, with a 3D sample preview in daylight and warm indoor light.

- `index.html` — the page (static, no build step; three.js 0.165.0 from jsDelivr).
- `swatches.json` — the colour list. Generated from the 3DxDor Management Hub; contains no brands, costs, quantities or sources.

To update: regenerate `swatches.json` from the Hub and commit it. Hebrew colour/finish names come from `tools/he.json`; the generator lists any new name missing a translation. GitHub Pages serves `main` from the repository root.

## Colour card (PDF)

`colours-he.pdf` — Hebrew A4 card of every colour in `swatches.json`, grouped by material, with availability and a QR code to this page.
Rebuild after each refresh: `python3 tools/card.py` (needs `qrcode` and Playwright/Chromium). Heebo font files are in `tools/fonts` (SIL OFL).

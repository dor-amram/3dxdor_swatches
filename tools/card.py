"""Build the Hebrew A4 colour card (PDF) from swatches.json.

Usage (repo root):  python3 tools/card.py
Needs: qrcode, playwright (Chromium). Output: colours-he.pdf
The card is a flat print reference; finishes (CF, wood, silk...) are shown by name, not rendered.
"""
import base64, colorsys, io, json, os, sys
import qrcode, qrcode.image.svg
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'https://dor-amram.github.io/3dxdor_swatches/'
OUT = os.path.join(ROOT, 'colours-he.pdf')

data = json.load(open(os.path.join(ROOT, 'swatches.json'), encoding='utf8'))
items = data['items']

# ---- same grouping as index.html
def type_group(t):
    if t == 'Resin': return 'Resin'
    if t == 'PLA': return 'PLA'
    if t in ('PETG', 'PCTG', 'PET'): return 'PETG'
    if t in ('ABS', 'ASA', 'HIPS'): return 'ABS'
    if t in ('TPU', 'Flex', 'PEBA'): return 'TPU'
    return 'ENG'

GROUPS = [('PLA', 'PLA'), ('PETG', 'PETG / PCTG'), ('ABS', 'ABS / ASA'), ('TPU', 'גמיש'), ('ENG', 'הנדסי'), ('Resin', 'שרף (הדפסת רזין)')]
FAM_ORDER = ['white', 'beige', 'yellow', 'orange', 'red', 'pink', 'purple', 'blue', 'green', 'brown', 'grey', 'black']

def family(it):
    if it['e'] == 'clear' and any(w in it['name'].lower() for w in ('clear', 'transparent', 'crystal', 'natural')):
        return 'white'
    h = (it.get('hex') or '#888888').lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, l, s = colorsys.rgb_to_hls(r, g, b); hh *= 360
    if s < .14 or (s < .25 and (l > .88 or l < .14)):
        return 'white' if l > .82 else 'black' if l < .2 else 'grey'
    if l < .16: return 'black'
    if l > .93: return 'white'
    if 18 <= hh < 50 and s < .5 and l > .6: return 'beige'
    if 8 <= hh < 45 and l < .42 and s < .75: return 'brown'
    if hh < 15 or hh >= 345: return 'pink' if l > .72 else 'red'
    if hh < 40: return 'orange'
    if hh < 68: return 'yellow'
    if hh < 170: return 'green'
    if hh < 255: return 'blue'
    if hh < 290: return 'purple'
    return 'pink'

AV = {'in': ('במלאי', '#23854F'), 'limited': ('כמות מוגבלת', '#C25A10'), 'order': ('בהזמנה', '#7046B0')}

def esc(s):
    return str(s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def swatch_style(it):
    hs = it.get('hexes') or []
    if len(hs) > 1:
        if it['e'] == 'gradient':
            return 'background:linear-gradient(135deg,%s)' % ','.join(hs)
        k = len(hs)
        return 'background:linear-gradient(135deg,%s)' % ','.join('%s %g%% %g%%' % (h, 100 * i / k, 100 * (i + 1) / k) for i, h in enumerate(hs))
    c = it.get('hex') or '#999999'
    if it['e'] == 'clear':  # translucent: tint over a light check so it reads as see-through
        return 'background:linear-gradient(%s99,%s99),repeating-conic-gradient(#d8d8d8 0 25%%,#fff 0 50%%) 0 0/3mm 3mm' % (c, c)
    return 'background:' + c

def font_face():
    d = os.path.join(ROOT, 'tools', 'fonts'); css = ''
    for w in (400, 500, 700):
        for sub, rng in (('hebrew', 'U+0590-05FF,U+200C-2010,U+20AA,U+25CC,U+FB1D-FB4F'), ('latin', 'U+0000-00FF,U+2000-206F,U+2190-21FF')):
            b = base64.b64encode(open(os.path.join(d, 'heebo-%s-%d-normal.woff2' % (sub, w)), 'rb').read()).decode()
            css += "@font-face{font-family:Heebo;font-weight:%d;src:url(data:font/woff2;base64,%s) format('woff2');unicode-range:%s}" % (w, b, rng)
    return css

def qr_svg():
    img = qrcode.make(URL, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=0)
    buf = io.BytesIO(); img.save(buf); return buf.getvalue().decode()

def cell(it):
    av, col = AV[it['avail']]
    sub = it['type'] + (' · ' + it['fin'] if it.get('fin') else '')
    return ('<div class="c"><div class="sw" style="%s"></div><div class="nm" dir="ltr">%s</div>'
            '<div class="mt" dir="ltr">%s</div><div class="av" style="color:%s">%s</div></div>') % (
        swatch_style(it), esc(it['name']), esc(sub), col, av)

sections = ''
for key, title in GROUPS:
    grp = [i for i in items if type_group(i['type']) == key]
    if not grp: continue
    grp.sort(key=lambda i: (FAM_ORDER.index(family(i)), i['name'].lower(), i['type'], i.get('fin') or ''))
    sections += '<section><h2><bdi>%s</bdi> <span>(%d צבעים)</span></h2><div class="g">%s</div></section>' % (esc(title), len(grp), ''.join(cell(i) for i in grp))

y, m, d = data['updated'].split('-')
counts = {k: sum(1 for i in items if i['avail'] == k) for k in AV}
legend = ''.join('<span><i style="background:%s"></i>%s</span>' % (c, n) for n, c in AV.values())

html = '''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>3DxDor · צבעים וחומרים</title><style>
%s
@page{size:A4;margin:11mm 10mm 13mm}
*{box-sizing:border-box}
body{margin:0;font-family:Heebo,sans-serif;color:#24222F;font-size:8.2pt;-webkit-print-color-adjust:exact;print-color-adjust:exact}
header{display:flex;align-items:center;gap:6mm;padding:5mm 6mm;border-radius:4mm;background:#F8CFA9;margin-bottom:4mm}
header .t{flex:1}
h1{margin:0;font-size:20pt;font-weight:700;line-height:1.1}
h1 b{color:#B8452C} h1 .en{direction:ltr;unicode-bidi:isolate}
header p{margin:1.5mm 0 0;font-size:9pt;color:#6B4632;line-height:1.35}
.qr{width:40mm;flex:none;text-align:center;font-size:6.6pt;color:#6B4632;white-space:nowrap}
.qr svg{width:24mm;height:24mm;display:block;margin:0 auto 1mm;background:#fff;padding:1.5mm;border-radius:2mm}
.meta{display:flex;gap:5mm;flex-wrap:wrap;align-items:center;margin:0 0 3mm;font-size:8pt;color:#67637A}
.meta i{display:inline-block;width:2.4mm;height:2.4mm;border-radius:50%%;margin-inline-end:1.2mm;vertical-align:middle}
section{margin-top:3mm}
h2{font-size:12pt;margin:0 0 2mm;padding-bottom:1mm;border-bottom:.3mm solid #E0DCEA;break-after:avoid}
h2 span{font-size:8pt;font-weight:400;color:#67637A;margin-inline-start:2mm}
.g{display:grid;grid-template-columns:repeat(8,1fr);gap:2.2mm 1.8mm}
.c{break-inside:avoid;min-width:0}
.sw{height:11.5mm;border-radius:1.6mm;box-shadow:inset 0 0 0 .25mm rgba(0,0,0,.18)}
.nm{font-weight:600;font-size:7.8pt;line-height:1.15;margin-top:1mm;overflow-wrap:anywhere;text-align:right}
.mt{font-size:6.6pt;color:#67637A;line-height:1.15;text-align:right}
.av{font-size:6.6pt;font-weight:500}
.foot{margin-top:5mm;font-size:7.4pt;color:#67637A;border-top:.3mm solid #E0DCEA;padding-top:2mm}
</style></head><body>
<header><div class="t"><h1><span class="en">3Dx<b>Dor</b></span> · צבעים וחומרים</h1>
<p>הפילמנטים והשרפים שיש לנו כרגע. סרקו את הקוד לתצוגת תלת־ממד של כל צבע באור יום ובתאורה ביתית חמה, ובחרו את הצבעים שאהבתם.</p></div>
<div class="qr">%s<div dir="ltr">dor-amram.github.io/3dxdor_swatches</div></div></header>
<div class="meta">%s<span>עודכן: %s.%s.%s</span><span>%d צבעים</span></div>
%s
<div class="foot">הצבעים בדף משוערים ונראים אחרת בכל מסך ומדפסת. גימורים מיוחדים (סיבי פחמן, עץ, משי, נצנצים) מוצגים כאן כצבע אחיד. לעבודה שבה הצבע קריטי, בקשו דוגמה מודפסת.</div>
</body></html>''' % (font_face(), qr_svg(), legend, d, m, y, len(items), sections)

src = os.path.join(ROOT, 'tools', 'card_he.html')
open(src, 'w', encoding='utf8').write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); pg.goto('file://' + src); pg.wait_for_timeout(400)
    pg.pdf(path=OUT, format='A4', print_background=True, prefer_css_page_size=True, display_header_footer=True,
           header_template='<span></span>',
           footer_template='<div style="width:100%;font-size:7pt;color:#888;text-align:center;font-family:sans-serif"><span class="pageNumber"></span> / <span class="totalPages"></span></div>')
    b.close()
os.remove(src)
print('wrote', OUT, 'items', len(items), counts)

#!/usr/bin/env python3
"""Scoped cumulative record print fix for assembled www/index.html; fails closed."""
from pathlib import Path
import re, base64
p = Path('www/index.html')
s = p.read_text(encoding='utf-8')
pattern = r'(cumulativeFrame:")([A-Za-z0-9+/=]+)(")'
m = re.search(pattern, s)
if not m:
    raise SystemExit('STOP: cumulativeFrame module not found. No changes made.')
h = base64.b64decode(m.group(2)).decode('utf-8')
if not all('id="p%d"' % i in h for i in range(1,12)):
    raise SystemExit('STOP: expected 11 pages missing. No changes made.')
marker='id="dnyanada-cumulative-print-11page-v1"'
if marker in h:
    print('11-page print fix already present; no change')
    raise SystemExit(0)
css = '''<style id="dnyanada-cumulative-print-11page-v1">
/* Only cumulative record print; undo screen-only active-page hiding. */
@media print {
  @page { size: A4 portrait; margin: 7mm; }
  html, body { overflow: visible !important; height: auto !important; }
  body.gy-cum-viewer-mode > main { display: block !important; overflow: visible !important; height: auto !important; }
  body.gy-cum-viewer-mode main .page:not(.printing),
  body.gy-cum-viewer-mode main .page.active:not(.printing) { display: none !important; }
  body.gy-cum-viewer-mode main .page.printing,
  body.gy-cum-viewer-mode main .page.printing:not(.active) {
    display: block !important;
    visibility: visible !important;
    position: relative !important;
    width: 100% !important;
    max-width: 100% !important;
    height: auto !important;
    overflow: visible !important;
    margin: 0 !important;
    box-shadow: none !important;
    break-before: auto !important;
    page-break-before: auto !important;
    break-after: page !important;
    page-break-after: always !important;
  }
  body.gy-cum-viewer-mode main .page.printing:last-of-type {
    break-after: auto !important;
    page-break-after: auto !important;
  }
}
</style>'''
if h.lower().count('</head>') != 1:
    raise SystemExit('STOP: unexpected cumulative HTML head structure. No changes made.')
h = re.sub(r'</head>', css + '</head>', h, count=1, flags=re.I)
encoded=base64.b64encode(h.encode('utf-8')).decode('ascii')
s2=s[:m.start(2)]+encoded+s[m.end(2):]
assert len(s2)>len(s) and s2.count('cumulativeFrame:"')==s.count('cumulativeFrame:"')
p.write_text(s2, encoding='utf-8')
print('OK: cumulative record 11-page print CSS fix inserted; other modules unchanged.')

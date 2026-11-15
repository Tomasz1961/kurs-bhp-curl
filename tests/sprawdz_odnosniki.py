#!/usr/bin/env python3
"""Kontrola odnośników strony (audyt stanu 15.11.2026, C-04): każdy odnośnik względny w index.html
(href/src, bez http(s), #, mailto:, data:, javascript:) musi wskazywać plik istniejący w repozytorium.
Strona pełna jest szyfrowana; jej odnośniki do kart charakterystyki (../sds/) sprawdza budowa przed szyfrowaniem."""
import os, re, sys, html
from urllib.parse import unquote
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
h = open(os.path.join(ROOT, 'index.html'), encoding='utf8').read()
h = re.sub(r'<script\b[^>]*>.*?</script>', lambda m: m.group(0) if 'href="' in m.group(0) else '', h, flags=re.S)
cele = set()
for a in re.findall(r'(?:href|src)="([^"]+)"', h):
    a = html.unescape(a).split('#')[0].split('?')[0]
    if not a or re.match(r'(https?:|mailto:|tel:|data:|javascript:|blob:|\$\{)', a): continue
    cele.add(unquote(a))
istnieje = lambda c: os.path.isfile(os.path.join(ROOT, c, 'index.html') if c.endswith('/') else os.path.join(ROOT, c))
brak = sorted(c for c in cele if not istnieje(c))
sds = sorted(c for c in cele if c.startswith('sds/'))
print(f'odnośników względnych: {len(cele)}, w tym kart charakterystyki: {len(sds)}, brakujących plików: {len(brak)}')
for b in brak: print('  BRAK:', b)
sys.exit(1 if brak or len(sds) < 20 else 0)

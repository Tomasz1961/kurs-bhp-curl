#!/usr/bin/env python3
"""Kontrola odnośników strony (audyt stanu 15.11.2026, C-04): każdy odnośnik względny w index.html
musi wskazywać plik istniejący w repozytorium.
Znaczniki czyta parser HTML (atrybuty href/src w cudzysłowach podwójnych, pojedynczych i bez cudzysłowów;
także <script src>, <link href>, <img src>). Odnośniki składane w skryptach strony (href="…"/href='…' w tekście skryptu)
są czytane osobno; odnośniki z wstawkami ${…} albo sklejane operatorem + są pomijane, bo powstają dopiero w przeglądarce.
Strona pełna jest szyfrowana; jej odnośniki do kart charakterystyki (../sds/) sprawdza budowa przed szyfrowaniem.
Użycie: sprawdz_odnosniki.py [plik_html [katalog_główny]] (domyślnie index.html repozytorium)."""
import os, re, sys, html
from html.parser import HTMLParser
from urllib.parse import unquote
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLIK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'index.html')
ROOT = sys.argv[2] if len(sys.argv) > 2 else (ROOT if len(sys.argv) < 2 else os.path.dirname(os.path.abspath(PLIK)))
POMIN = re.compile(r'(https?:|//|mailto:|tel:|data:|javascript:|blob:|about:|#|\$\{)', re.I)

class Zbieracz(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.cele = []; self.skrypty = []; self._w_skrypcie = False
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ('href', 'src') and v is not None: self.cele.append(v)
        self._w_skrypcie = tag in ('script', 'style')
    handle_startendtag = handle_starttag
    def handle_endtag(self, tag): self._w_skrypcie = False
    def handle_data(self, d):
        if self._w_skrypcie: self.skrypty.append(d)

z = Zbieracz(); z.feed(open(PLIK, encoding='utf8').read()); z.close()
surowe = list(z.cele)
for s in z.skrypty:  # odnośniki zapisane w skryptach jako tekst HTML
    surowe += [m.group(2) for m in re.finditer(r'''(?:href|src)=\\?(["'])(.*?)\\?\1''', s)]
cele = set()
for a in surowe:
    a = html.unescape(a.strip())
    if not a or POMIN.match(a) or '${' in a or re.search(r"['\"]\s*\+|\+\s*['\"]", a): continue  # składane w skrypcie z części
    a = a.split('#')[0].split('?')[0]
    if a: cele.add(unquote(a))
def istnieje(c):
    p = os.path.normpath(os.path.join(ROOT, c))
    return os.path.isfile(os.path.join(p, 'index.html')) if c.endswith('/') else os.path.isfile(p)
brak = sorted(c for c in cele if not istnieje(c))
sds = sorted(c for c in cele if c.startswith('sds/'))
print(f'odnośników względnych: {len(cele)}, w tym kart charakterystyki: {len(sds)}, brakujących plików: {len(brak)}')
for b in brak: print('  BRAK:', b)
min_sds = int(os.environ.get('MIN_SDS', '20'))
sys.exit(1 if brak or len(sds) < min_sds else 0)

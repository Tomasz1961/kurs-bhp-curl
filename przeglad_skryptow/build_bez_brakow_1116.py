#!/usr/bin/env python3
"""Krok 11zz10 (16.11.2026): listy braków poza kursem – TS 16.11.2026 20:21:22 UTC (decyzja 153):
„nie pokazujmy teraz tego Grzegórskiej, tylko jest to nasz wewnętrzny panel … zahasłowany osobnym hasłem … z przydzieleniem
odpowiedzialności, bo kierownicy muszą te karty zdobyć”.
Kurs (claude.ai, www publiczna, /pelny/, /pracownik/) nie pokazuje list braków. Dane zostają w bazie (soi_luka, karty ryzyka osób,
karty charakterystyki); panel wewnętrzny z osobnym hasłem i odpowiedzialnością kierowników buduje wątek systemu BHP.
Usunięte z pliku kursu (nie ukryte – treść /pelny/ jest odszyfrowana w przeglądarce, ukrycie CSS nic nie chroni):
 1) w zakładce ŚOI blok „Braki w rejestrze (do uzupełnienia)” (h3 + opis + tabela z soi_luka);
 2) w tabeli osób zakładki Karty oceny ryzyka napis „brak karty – do uzupełnienia przez dział BHP IUNG-PIB” → „—”.
Po kroku: STOP, gdy w treści kursu zostanie „Braki w rejestrze” albo „brak karty – do uzupełnienia”. Działa na końcu łańcucha
(po krokach, które te bloki odtwarzają). Idempotentne, bez LLM."""
import re, sqlite3, os, sys
B = '/mnt/project-files/bhp'
P = sys.argv[1] if len(sys.argv) > 1 else f'{B}/kurs_online/kurs_bhp_curl.html'
h = open(P, encoding='utf-8').read(); h0 = h
ZN = '<!--BRAKI-WEWN-1116: lista braków ŚOI w panelu wewnętrznym (dec. 153)-->'
i = h.find('<h3>Braki w rejestrze (do uzupełnienia)</h3>')
if i >= 0:
    j = h.find('</table></div>', i)
    assert 0 < j - i < 20000, 'STOP 11zz10: koniec tabeli braków ŚOI'
    USUN = h[i:j + len('</table></div>')]
    h = h[:i] + ZN + h[j + len('</table></div>'):]
    if len(sys.argv) <= 1:  # treść usunięta zapisana w bazie: krok 11zt rozpoznaje swoje zamiany w usuniętym bloku (jak przy 11zz4)
        _c = sqlite3.connect(os.environ.get('BHP_DB', f'{B}/bhp_rejestr.sqlite'))
        _c.execute('create table if not exists kurs_fragment_usuniety(krok text primary key, fragment text, powod text, data text)')
        _c.execute("insert or replace into kurs_fragment_usuniety values('11zz10 ŚOI: braki w rejestrze', ?, 'lista braków – panel wewnętrzny (dec. 153)', date('now'))", (USUN,))
        _c.commit(); _c.close()
n_karta = h.count('brak karty – do uzupełnienia przez dział BHP IUNG-PIB')
h = h.replace('<td>brak karty – do uzupełnienia przez dział BHP IUNG-PIB</td>', '<td>—</td>')
for w in ('Braki w rejestrze', 'brak karty – do uzupełnienia'):
    assert w not in h, f'STOP 11zz10: „{w}” nadal w kursie'
# blok usunięty wcześniej (kurs już bez niego): treść z kopii zapisanej przy pierwszym usunięciu (zrodla/kurs_usuniety_11zz10_soi_braki.html)
_ZF = f'{B}/zrodla/kurs_usuniety_11zz10_soi_braki.html'
if len(sys.argv) <= 1 and i < 0 and os.path.exists(_ZF):
    _c = sqlite3.connect(os.environ.get('BHP_DB', f'{B}/bhp_rejestr.sqlite'))
    _c.execute('create table if not exists kurs_fragment_usuniety(krok text primary key, fragment text, powod text, data text)')
    if not _c.execute("select count(*) from kurs_fragment_usuniety where krok='11zz10 ŚOI: braki w rejestrze'").fetchone()[0]:
        _c.execute("insert into kurs_fragment_usuniety values('11zz10 ŚOI: braki w rejestrze', ?, 'lista braków – panel wewnętrzny (dec. 153)', date('now'))", (open(_ZF, encoding='utf-8').read(),))
    _c.commit(); _c.close()
if h != h0: open(P, 'w', encoding='utf-8').write(h)
if len(sys.argv) <= 1:
    c = sqlite3.connect(os.environ.get('BHP_DB', f'{B}/bhp_rejestr.sqlite'))
    cyt = open(f'{B}/zrodla/ts_2026-11-16_2021_panel_wewnetrzny.txt', encoding='utf-8').read().strip()
    c.execute("""insert or ignore into decyzja_ts(id, czas_utc, cytat, decyzja, wdrozenie, status, zrodlo) values(153, '2026-11-16T20:21:22Z', ?,
     'Listy braków (karty charakterystyki, braki ŚOI, przeterminowane, brak karty ryzyka) nie są pokazywane w kursie ani p. Grzegórskiej. Idą do wewnętrznego panelu z osobnym hasłem, z przypisaną odpowiedzialnością kierowników (Wala, Szlosarczyk, ew. Pecio); panel buduje wątek systemu BHP.',
     'krok 11zz10 build_bez_brakow_1116.py (kurs bez list braków); kontrola D-153; panel – wątek systemu BHP', 'WDROZONE_W_PLIKU',
     'czat projektu, TS 16.11.2026 20:21:22 UTC (cmsg_01LjRRUGCMRdzeCLcFKfUaaM8kMVXYwQpX9XckaXhvwBge); zrodla/ts_2026-11-16_2021_panel_wewnetrzny.txt')""", (cyt,))
    c.commit(); c.close()
print(f'11zz10 listy braków poza kursem: kurs {"zmieniony" if h != h0 else "bez zmian"} | „brak karty” zamienionych {n_karta}')

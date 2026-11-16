#!/usr/bin/env python3
"""Test negatywny każdej kontroli poleceń (profil modelu, reguła P-01: każda reguła ma „test negatywny”). Bez LLM.
Dla każdej kontroli z kontrole_def.K budujemy celowo zepsuty stan i sprawdzamy, że ta sama kontrola daje wynik niezaliczony:
  html / tekst, wymagane > 0  → z kursu usunięte wszystkie trafienia wzorca;
  html / tekst, wymagane = 0  → do kursu wstawiony tekst pasujący do wzorca (gdy wzorzec da się zapisać dosłownie);
  sql_bhp / inwentarz / sql_adm, wymagane > 0 → zapytanie na kopii bazy w pamięci z usuniętymi wszystkimi wierszami
  (kontrola istnienia tabeli → kopia bez tej tabeli);
  sql, wymagane = 0 (brak naruszeń) → kopia z dopisanym wierszem bez danych; test jest, gdy taki wiersz daje wynik niezaliczony;
  plik, wymagane > 0 → szukanie w pustym katalogu;  admin, wymagane > 0 → pusty plik danych prowadzącego;
  skrypt → skrypt z własnym testem negatywnym w każdym przebiegu (lista SKRYPT_TEST).
Kontrole bez możliwego testu tą drogą (sprawdzenia „brak naruszeń” w bazie, eksport, po wysyłce) dostają „brak” – zostają brakiem profilu.
Wynik WYKRYTO / NIE WYKRYTO / brak w tabeli kontrola_test_negatywny. NIE WYKRYTO = kontrola nic nie sprawdza → STOP (kod 1).
Użycie: test_negatywny_kontroli.py <kurs.html>"""
import os, re, sys, html, sqlite3, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kontrole_def import K
B = '/mnt/project-files/bhp'
# skrypty kontroli, które same w każdym przebiegu wykonują test negatywny i kończą się błędem, gdy go nie wykryją
SKRYPT_TEST = {'kontrola_jezyk': 'wstrzyknięte słowo niedozwolone, błędny skrypt strony, znacznik dopisany do zaświadczenia',
               'kontrola_qr_kurs': '7 testów kodów QR: zmieniona treść, brak kodu, kod spoza rejestru',
               'test_mapy': '20 wstrzykniętych naruszeń mapy bezpieczeństwa',
               'silnik_mapy': '20 wstrzykniętych naruszeń mapy bezpieczeństwa (test_mapy.py)',
               'przyjmij_podpisane': 'skan dla nieistniejącej osoby nie może dać stanu PODPISANY',
               'test_stalosci': 'drugi przebieg poprawek nie może zmienić kursu'}

def spelnia(v, ocz):
    m = re.fullmatch(r'(>=|<=|=|>|<)(\d+)', ocz or '')
    if not m: return None
    op, n = m.group(1), int(m.group(2))
    return {'>=': v >= n, '<=': v <= n, '=': v == n, '>': v > n, '<': v < n}[op]

def wymaga_tresci(ocz):
    return spelnia(0, ocz) is False  # wynik 0 jest niezaliczony → kontrola wymaga obecności

def _gen(items):
    """Najkrótszy tekst pasujący do sparsowanego wzorca (re._parser); skróty: cyfra 1, litera a, odstęp spacja."""
    import re._constants as C
    out = []
    for op, av in items:
        if op is C.LITERAL: out.append(chr(av))
        elif op is C.NOT_LITERAL: out.append('a' if chr(av) != 'a' else 'b')
        elif op is C.ANY: out.append('a')
        elif op is C.IN:
            x = av[0]
            if x[0] is C.NEGATE: out.append('a' if not any(o is C.LITERAL and v == ord('a') for o, v in av[1:]) else 'x')
            elif x[0] is C.LITERAL: out.append(chr(x[1]))
            elif x[0] is C.RANGE: out.append(chr(x[1][0]))
            elif x[0] is C.CATEGORY: out.append({C.CATEGORY_DIGIT: '1', C.CATEGORY_SPACE: ' '}.get(x[1], 'a'))
            else: return None
        elif op is C.BRANCH: r = _gen(av[1][0]); out.append(r if r is not None else '')
        elif op is C.SUBPATTERN: r = _gen(av[-1]); out.append(r or '')
        elif op in (C.MAX_REPEAT, C.MIN_REPEAT, getattr(C, 'POSSESSIVE_REPEAT', None)):
            r = _gen(av[2]); out.append((r or '') * max(av[0], 0))
        elif op in (C.AT, C.ASSERT, C.ASSERT_NOT): pass
        elif op is C.CATEGORY: out.append({C.CATEGORY_DIGIT: '1', C.CATEGORY_SPACE: ' '}.get(av, 'a'))
        else: return None
    return ''.join(out)

def doslownie(wyr):
    """Tekst pasujący do wzorca (zbudowany z wzorca i sprawdzony nim); None, gdy nie da się go zbudować."""
    try:
        import re._parser as P
        s = _gen(P.parse(wyr))
    except Exception:
        return None
    if not s: return None
    return s if re.search(wyr, ' ' + s + ' ') else None

def pusta_kopia(src_uri):
    z = sqlite3.connect(src_uri, uri=True); m = sqlite3.connect(':memory:'); z.backup(m); z.close()
    m.execute('PRAGMA foreign_keys=OFF')
    for (t,) in m.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'").fetchall():
        m.execute(f'DELETE FROM "{t}"')
    return m

def wiersz_pusty(src_uri, wyr):
    """Kopia bazy z dopisanym do sprawdzanej tabeli wierszem bez danych (puste pola, nowy klucz). Wynik: (baza, tabela) albo None."""
    m0 = re.search(r'\bfrom\s+"?(\w+)', wyr)
    if not m0: return None
    t = m0.group(1)
    z = sqlite3.connect(src_uri, uri=True); m = sqlite3.connect(':memory:'); z.backup(m); z.close()
    if not m.execute("select 1 from sqlite_master where type='table' and name=?", (t,)).fetchone(): return None
    m.execute('PRAGMA foreign_keys=OFF'); m.execute('PRAGMA ignore_check_constraints=ON')
    kol = m.execute(f'pragma table_info("{t}")').fetchall(); wz = m.execute(f'select * from "{t}" limit 1').fetchone()
    w = []
    for i, (cid, nazwa, typ, notnull, dflt, pk) in enumerate(kol):
        if pk:
            w.append((m.execute(f'select coalesce(max("{nazwa}"),0)+1000 from "{t}"').fetchone()[0]) if 'INT' in (typ or '').upper() else 'TEST_NEGATYWNY')
        elif notnull: w.append(wz[i] if wz else 'x')
        else: w.append(None)
    # wartości dosłowne z warunku zapytania (kol='wartość') – wiersz „bez danych” ma też status, którego kontrola zabrania (np. D-131 „DO WYKONANIA”)
    lit = dict(re.findall(r"(?<![!<>])\b(\w+)\s*=\s*'([^']*)'", wyr))
    # liczby dosłowne z warunku (np. blad=1, ok=0) – wiersz „bez danych” ma wartość, której kontrola zabrania (15.11.2026, D-101)
    for k, v in re.findall(r"(?<![!<>'\w])\b(\w+)\s*=\s*(-?\d+)\b(?!')", re.sub(r"'[^']*'", "''", wyr)):
        lit.setdefault(k, int(v))
    w = [lit.get(k[1], w[i]) if not k[5] else w[i] for i, k in enumerate(kol)]
    m.execute(f'insert into "{t}" values({",".join("?" * len(w))})', w)
    return m, t

def main():
    kurs = os.path.abspath(sys.argv[1]); raw = open(kurs, encoding='utf-8').read()
    tekst = html.unescape(re.sub(r'<script\b.*?</script>|<style\b.*?</style>', ' ', raw, flags=re.S))
    tekst = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', tekst))
    bhp0 = adm0 = None; pusty = tempfile.mkdtemp()
    wyn = []
    for nr, (pol, typ, wyr, ocz, opis) in enumerate(K, 1):
        sposob, ok = None, None
        try:
            if typ in ('html', 'tekst'):
                baza = raw if typ == 'html' else tekst
                if wymaga_tresci(ocz):
                    sposob = 'usunięte z kursu wszystkie trafienia wymaganej treści'; ok = spelnia(len(re.findall(wyr, re.sub(wyr, '', baza))), ocz)
                else:
                    s = doslownie(wyr)
                    if s is not None:
                        sposob = 'wstawiony do kursu niedozwolony tekst zbudowany z wzorca (tekstu nie zapisujemy – mógłby sam naruszać inne kontrole)'; ok = spelnia(len(re.findall(wyr, baza + ' ' + s + ' ')), ocz)
            elif typ in ('sql_bhp', 'inwentarz') and wymaga_tresci(ocz) and 'sqlite_master' in wyr:
                m = pusta_kopia(f'file:{B}/bhp_rejestr.sqlite?mode=ro'); nazwy = re.findall(r"name\s*=\s*'([^']+)'", wyr)
                for n in nazwy: m.execute(f'DROP TABLE IF EXISTS "{n}"'); m.execute(f'DROP VIEW IF EXISTS "{n}"')
                sposob = 'kopia rejestru BHP bez wymaganej tabeli ' + ', '.join(nazwy); ok = spelnia((m.execute(wyr).fetchone() or [0])[0] or 0, ocz)
            elif typ in ('sql_bhp', 'inwentarz') and wymaga_tresci(ocz):
                bhp0 = bhp0 or pusta_kopia(f'file:{B}/bhp_rejestr.sqlite?mode=ro')
                sposob = 'zapytanie na kopii rejestru BHP bez żadnych wierszy'
                ok = spelnia((bhp0.execute(wyr.replace('{kurs_sha}', 'x')).fetchone() or [0])[0] or 0, ocz)
            elif typ == 'inwentarz' and re.search(r"status in \('BEZ DECYZJI'", wyr):
                # element GPT bez decyzji: kopia rejestru z dopisanym elementem o stanie „BEZ DECYZJI” (wiersz pusty nie ma stanu – nic by nie sprawdził)
                z = sqlite3.connect(f'file:{B}/bhp_rejestr.sqlite?mode=ro', uri=True); m = sqlite3.connect(':memory:'); z.backup(m); z.close()
                m.execute("insert into gpt_inwentarz(id, status) values('TEST-NEGATYWNY-BEZ-DECYZJI', 'BEZ DECYZJI')")
                sposob = 'dopisany element GPT bez decyzji (stan „BEZ DECYZJI”)'; ok = spelnia((m.execute(wyr).fetchone() or [0])[0] or 0, ocz)
            elif typ == 'sql_bhp' and pol == 'D-143' and 'from ilustracja' in wyr and not wymaga_tresci(ocz):
                # D-143: dopisana ilustracja ze stanem wpisanym ręcznie („w kursie”) i oznaczona jako poza wydaniem (wiersz pusty nie ma stanu – nic by nie sprawdził)
                z = sqlite3.connect(f'file:{B}/bhp_rejestr.sqlite?mode=ro', uri=True); m = sqlite3.connect(':memory:'); z.backup(m); z.close()
                m.execute("insert into ilustracja(id, status) values('TEST-NEGATYWNY-ILUSTRACJA', 'w kursie')")
                m.execute("insert or replace into obraz_poza_wydaniem(ident, fragment, sha256, data, aktualne) values('TEST-NEGATYWNY-ILUSTRACJA', 'x', 'x', 'x', 1)")
                sposob = 'dopisana ilustracja ze stanem „w kursie” wpisanym ręcznie, oznaczona jako poza wydaniem'; ok = spelnia((m.execute(wyr).fetchone() or [0])[0] or 0, ocz)
            elif typ in ('sql_bhp', 'inwentarz', 'sql_adm') and not wymaga_tresci(ocz) and spelnia(1, ocz) is False:
                src = f'file:{B}/bhp_rejestr.sqlite?mode=ro' if typ != 'sql_adm' else 'file:/mnt/project-files/adm/adm.sqlite?mode=ro'
                r = wiersz_pusty(src, wyr.replace('{kurs_sha}', 'x'))
                if r and spelnia((r[0].execute(wyr.replace('{kurs_sha}', 'x')).fetchone() or [0])[0] or 0, ocz) is False:
                    sposob = f'dopisany do tabeli {r[1]} wiersz bez danych'; ok = False
            elif typ == 'sql_adm' and wymaga_tresci(ocz):
                adm0 = adm0 or pusta_kopia('file:/mnt/project-files/adm/adm.sqlite?mode=ro')
                sposob = 'zapytanie na kopii bazy kadr bez żadnych wierszy'; ok = spelnia((adm0.execute(wyr).fetchone() or [0])[0] or 0, ocz)
            elif typ == 'plik' and wymaga_tresci(ocz):
                sposob = 'szukanie wymaganych plików w pustym katalogu'
                import glob; ok = spelnia(len(glob.glob(os.path.join(pusty, wyr), recursive=True)), ocz)
            elif typ == 'admin' and wymaga_tresci(ocz):
                sposob = 'pusty plik danych prowadzącego'; ok = False
            elif typ == 'admin':
                s_ = doslownie(wyr)
                if s_ is not None:
                    sposob = 'do danych prowadzącego wstawiony niedozwolony tekst zbudowany z wzorca'; ok = spelnia(len(re.findall(wyr, ' ' + s_ + ' ')), ocz)
            elif typ == 'skrypt':
                for k, t in SKRYPT_TEST.items():
                    if k in wyr: sposob = 'test wbudowany w skrypt: ' + t; ok = False; break
                else:
                    if re.fullmatch(r'grep -q "[^"]+" /mnt/project-files/\S+( && grep -q "[^"]+" /mnt/project-files/\S+)*', wyr):
                        pusty_plik = os.path.join(pusty, 'pusty.txt'); open(pusty_plik, 'w').close()
                        import subprocess
                        r = subprocess.run(re.sub(r'/mnt/project-files/\S+', pusty_plik, wyr), shell=True, cwd=pusty)
                        sposob = 'wymagany zapis szukany w pustym pliku'; ok = r.returncode == 0
        except Exception as e:
            sposob, ok = f'błąd w zepsutym stanie ({str(e)[:80]}) – kontrola daje wynik niezaliczony', False
        wynik = 'brak' if sposob is None else ('WYKRYTO' if ok is False else 'NIE WYKRYTO')
        wyn.append((nr, pol, typ, opis, sposob, wynik))
    w = sqlite3.connect(f'{B}/bhp_rejestr.sqlite')
    w.executescript('''DROP TABLE IF EXISTS kontrola_test_negatywny;
      CREATE TABLE kontrola_test_negatywny(nr INTEGER PRIMARY KEY, polecenie TEXT, typ TEXT, opis TEXT, sposob TEXT,
        wynik TEXT CHECK(wynik IN ('WYKRYTO','NIE WYKRYTO','brak')));''')
    w.executemany('insert into kontrola_test_negatywny values(?,?,?,?,?,?)', wyn); w.commit()
    lic = {k: sum(1 for x in wyn if x[5] == k) for k in ('WYKRYTO', 'NIE WYKRYTO', 'brak')}
    print(f"test negatywny kontroli: {len(wyn)} kontroli | wykryto {lic['WYKRYTO']} | nie wykryto {lic['NIE WYKRYTO']} | bez testu {lic['brak']}")
    for x in wyn:
        if x[5] == 'NIE WYKRYTO': print('  STOP kontrola nic nie sprawdza:', x[0], x[1], x[3])
    sys.exit(1 if lic['NIE WYKRYTO'] else 0)

if __name__ == '__main__':
    main()

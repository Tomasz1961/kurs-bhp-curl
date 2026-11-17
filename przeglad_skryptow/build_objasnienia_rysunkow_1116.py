#!/usr/bin/env python3
"""Krok 11zz11 (16.11.2026): objaśnienia rysunków widoczne dla uczestnika – TS 16.11.2026 20:12 (decyzja 150): „każdy obrazek, który
coś pokazuje, też musi być wyjaśnione, dlaczego to jest źle, a dlaczego to jest dobrze”; dec. 149 (bez wewnętrznych dopisków).
Podstawa: przegląd kursu 16.11.2026 (scratchpad przeglad_jezyk_obrazy.md): 1 z 68 rysunków ma widoczne „dobrze/źle i dlaczego”,
23 mają to tylko w ukrytym tekście alternatywnym; 61 podpisów kończy się dopiskiem z kontroli („Plansza szkoleniowa, sprawdzona…”).
Zmiany (poprawka na gotowym pliku, bez przebudowy; tekst wyłącznie z kursu – z atrybutu alt tej samej planszy):
 1) usunięty dopisek kontrolny „Plansza szkoleniowa, sprawdzona ze wzorcem…/ze wzorcami…/z treścią kursu i rejestrem ŚOI.” z podpisów;
 2) plansza z dwoma panelami, której alt ma „Prawidłowo|Dobrze|Właściwie: … Błędnie|Źle|Niewłaściwie: …”, a podpis nie ma części
    „źle”, dostaje pod podpisem widoczny akapit „Dobrze: … Źle: …” (z alt, z poprawioną podwójną kropką);
 3) z objaśnień odpowiedzi testu usunięty dopisek „(Pytanie scenariuszowe, do przeglądu.)”;
 4) blok „Plansze: dobrze i źle” modułu 12 przeniesiony z zakładki „rejestr” do modułu 12 (błąd kroku 11d2 przy ostatnim module).
Stan każdej planszy w tabeli obraz_objasnienie (sekcja, ident, ma_dobrze_zle_widoczne, zrodlo); plansze bez tekstu w kursie
→ stan „DO OPRACOWANIA” (kontrola D-150 pokazuje liczbę, tekst dopisuje się z treści kursu, nie z pamięci). Idempotentne, bez LLM."""
import re, sqlite3, os, sys, html as H, hashlib, base64
B = '/mnt/project-files/bhp'
P = sys.argv[1] if len(sys.argv) > 1 else f'{B}/kurs_online/kurs_bhp_curl.html'
s = open(P, encoding='utf-8').read(); s0 = s

# 1) dopiski kontrolne
s, n1 = re.subn(r'\s*Plansza szkoleniowa, sprawdzona (?:ze wzorcem ubioru strefy \(HIG-IN-002\)|ze wzorcami ubioru stref \([^)]*\))\.', '', s)
s, n1b = re.subn(r'Plansza szkoleniowa, sprawdzona z treścią kursu i rejestrem ŚOI\.\s*', '', s)
assert 'Plansza szkoleniowa, sprawdzona' not in s, 'STOP 11zz11: dopisek kontrolny w podpisie'

# 3) dopisek w objaśnieniach odpowiedzi
s, n3 = re.subn(r'\s*\(Pytanie scenariuszowe, do przeglądu\.\)', '', s)

# 4) blok m12 w module 12
a = s.find('<!--PLANSZE-V2-m12-->'); n4 = 0
if a >= 0:
    b = s.find('<!--PLANSZE-V2-m12-KONIEC-->', a) + len('<!--PLANSZE-V2-m12-KONIEC-->')
    m12 = s.find('<section id="m12"'); m12k = s.find('</section>', m12)
    if not (m12 < a < m12k):
        blk = s[a:b]; s = s[:a] + s[b:]
        m12 = s.find('<section id="m12"'); m12k = s.find('</section>', m12)
        s = s[:m12k] + blk + s[m12k:]; n4 = 1
    m12 = s.find('<section id="m12"'); m12k = s.find('</section>', m12)
    assert m12 < s.find('<!--PLANSZE-V2-m12-->') < m12k, 'STOP 11zz11: plansza m12 poza modułem 12'

# 2) dobrze/źle z alt do podpisu
POZ = r'(?:Prawidłowo|Dobrze|Właściwie)'; NEG = r'(?:Błędnie|Źle|Niewłaściwie)'
sek = [(m.start(), m.group(1)) for m in re.finditer(r'<section id="([^"]+)"', s)]
def sekcja(pos):
    r = None
    for p_, k in sek:
        if p_ <= pos: r = k
    return r
def czysc(t): return re.sub(r'\.{2,}', '.', re.sub(r'\s+', ' ', t)).strip(' .') + '.'
rej = []; n2 = 0; n5 = 0; n6 = 0
def tekst_sekcji(sec):
    i = s.find('<section id="%s"' % sec); j = s.find('</section>', i)
    t = re.sub(r'<script.*?</script>|<style.*?</style>|<figure.*?</figure>', ' ', s[i:j], flags=re.S)
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', t)))
OBJ = {}
TSV = f'{B}/dane/objasnienia_rysunkow.tsv'
for w in open(TSV, encoding='utf-8').read().rstrip('\n').split('\n')[1:]:
    k, sc_, dob, zle, cyt, dl = (w.split('\t') + [''])[:6]
    ts = tekst_sekcji(sc_)
    for c_ in cyt.split(' | '):
        assert c_.strip() in ts, f'STOP 11zz11: cytat do {k} nie występuje w module {sc_}: {c_[:80]}'
    OBJ[k] = (dob, zle, dl or cyt.split(' | ')[0])
# oznaczenie rysunku z rejestru obrazów (po skrócie obrazu) – klucz tabeli objaśnień dla plansz bez atrybutu data-* („m9:SCHEMAT_store”)
_rj = sqlite3.connect(f'file:{os.environ.get("BHP_DB", B + "/bhp_rejestr.sqlite")}?mode=ro', uri=True)
RYS = {sh: idt for idt, sh in _rj.execute("select ident, sha256_w_stronie from obraz_uzycie where strona like 'kurs%'")}; _rj.close()
n7 = 0; n8 = 0
def zamien(m):
    global n2, n5, n6, n7, n8
    f = m.group(0); sc = sekcja(m.start())
    ident = (re.search(r'data-(?:v2|gd|ident|img|id)="([^"]+)"', f) or re.search(r'id="([^"]+)"', f))
    ident = ident.group(1) if ident else f'{sc}#{m.start()}'
    # moduły m1–m12 oraz zakładka ŚOI (plansze modułu 5; uwaga Copilota do PR #16); skany kart ryzyka to dokumenty, nie plansze
    if not re.match(r'm\d+$|soi$', sc or ''): return f
    im0 = re.search(r'src="data:image/[a-z+]+;base64,([^"]+)"', f)
    rys = RYS.get(hashlib.sha256(base64.b64decode(im0.group(1))).hexdigest(), '') if im0 else ''
    klucz = ident if ident in OBJ else f'{sc}:{rys}'
    alt = re.search(r'alt="([^"]*)"', f); alt = H.unescape(alt.group(1)) if alt else ''
    cap = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', f, re.S)
    capt = re.sub(r'<[^>]+>', ' ', cap.group(1)) if cap else ''
    ma = bool(re.search(NEG + r'\s*:', capt)) or 'class="dz"' in f
    if not ma:
        g = re.search(POZ + r'\s*:\s*(.+?)\s*' + NEG + r'\s*:\s*(.+)$', alt, re.S)
        if g and cap:
            dob, zle = czysc(g.group(1)), czysc(g.group(2))
            dz = f'<span class="dz"><b>Dobrze:</b> {H.escape(dob)} <b>Źle:</b> {H.escape(zle)}</span>'
            f = f[:cap.end(1)] + ' ' + dz + f[cap.end(1):]; ma = True; n2 += 1
            zr = 'alt planszy (tekst kursu)'
        elif klucz in OBJ and OBJ[klucz][0] and cap:
            dob, zle, dl = OBJ[klucz]
            dz = f'<span class="dz"><b>Dobrze:</b> {H.escape(dob)}' + (f' <b>Źle:</b> {H.escape(zle)}' if zle else '') + f' <b>Dlaczego:</b> {H.escape(dl)}</span>'
            f = f[:cap.end(1)] + ' ' + dz + f[cap.end(1):]; ma = True; n5 += 1
            zr = 'dane/objasnienia_rysunkow.tsv (cytat z modułu sprawdzony)'
        elif cap and not re.search(r'Poprawn|Błędn|Błędne|Po prawej|Po lewej|' + NEG, alt):
            g = re.match(r'Prawidłowo\s*:\s*(.+?)(?:\s*Plansza przedstawia prawidłowy przebieg czynności\.?)?$', alt, re.S)
            if g and len(re.sub(r'\s+', ' ', capt).strip()) < 60:
                f = f[:cap.end(1)] + f' <span class="dz"><b>Jak postępować:</b> {H.escape(czysc(g.group(1)))}</span>' + f[cap.end(1):]; n6 += 1
            ma = len(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.search(r'<figcaption[^>]*>(.*?)</figcaption>', f, re.S).group(1))).strip()) >= 60
            zr = 'instrukcja krok po kroku – objaśnienie w podpisie' if ma else 'brak objaśnienia w kursie'
        else: zr = 'brak tekstu dobrze/źle w kursie'
    else:
        zr = 'podpis'
        # starsze podpisy „Właściwie: … Niewłaściwie: …” bez objaśnienia: ta sama treść jako „Dobrze / Źle” (uwaga Copilota do PR #17)
        if cap and 'class="dz"' not in f:
            c1 = cap.group(1)
            g = re.search(r'(?:Właściwie|Prawidłowo|Dobrze)\s*:\s*(.+?)\s*(?:Niewłaściwie|Błędnie|Źle)\s*:\s*(.+?)(?=\s*<span|\s*$)', c1, re.S)
            if g:
                c2 = (c1[:g.start()].rstrip() + ' ' + c1[g.end():].strip()).rstrip()
                c2 += f' <span class="dz"><b>Dobrze:</b> {g.group(1).strip()} <b>Źle:</b> {g.group(2).strip()}</span>'
                f = f[:cap.start(1)] + c2 + f[cap.end(1):]; n8 += 1
    # „Dlaczego” do istniejącego objaśnienia „Dobrze/Źle” (z tabeli objaśnień, cytat sprawdzony z modułem; uwaga Copilota do PR #16)
    dzm0 = re.search(r'<span class="dz">(.*?)</span>', f, re.S)
    if dzm0 and 'Dlaczego:' not in dzm0.group(1) and '<b>Źle:</b>' in dzm0.group(1) and klucz in OBJ:
        f = f[:dzm0.end(1)] + f' <b>Dlaczego:</b> {H.escape(OBJ[klucz][2])}' + f[dzm0.end(1):]; n7 += 1
    # tekst objaśnienia z gotowego podpisu (ten sam znak w znak, który widzi uczestnik) – dla innych silników (zapytanie systemu BHP 16.11.2026 23:16)
    cp = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', f, re.S); cp = cp.group(1) if cp else ''
    dzm = re.search(r'<span class="dz">(.*?)</span>', cp, re.S)
    txt = lambda t: re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', t))).strip()
    podp = txt(cp[:dzm.start()] if dzm else cp); czesci = {'Dobrze': '', 'Źle': '', 'Dlaczego': '', 'Jak postępować': ''}
    if dzm:
        for k_, v_ in re.findall(r'<b>(Dobrze|Źle|Dlaczego|Jak postępować):</b>(.*?)(?=<b>(?:Dobrze|Źle|Dlaczego|Jak postępować):</b>|$)', dzm.group(1), re.S): czesci[k_] = txt(v_)
    if zr == 'podpis' and dzm:   # drugi przebieg: źródło z treści objaśnienia, nie „podpis”
        zr = ('dane/objasnienia_rysunkow.tsv (cytat z modułu sprawdzony)' if czesci['Dlaczego'] else
              'instrukcja krok po kroku – objaśnienie w podpisie' if czesci['Jak postępować'] else 'alt planszy (tekst kursu)')
    im = re.search(r'src="data:image/[a-z+]+;base64,([^"]+)"', f)
    sha = hashlib.sha256(base64.b64decode(im.group(1))).hexdigest() if im else ''
    rej.append((sc, ident, 1 if ma else 0, zr if ma else 'brak tekstu dobrze/źle w kursie', sha, podp, czesci['Dobrze'], czesci['Źle'], czesci['Dlaczego'], czesci['Jak postępować']))
    return f
s = re.sub(r'<figure[^>]*>.*?</figure>', zamien, s, flags=re.S)
# styl objaśnień na stronie kursu (nie w szablonie wydruku fullDoc, gdzie trafił pierwszy przebieg przez „</head>” w tekście skryptu)
STYL = '<style>figcaption span.dz{display:block;margin-top:4px}</style>'
s = s.replace(STYL + '</head><body>${body}', '</head><body>${body}')
if not s.startswith('<meta charset="utf-8">'):
    # strona bez nagłówka <head>: deklaracja kodowania na początku pliku – bez niej przeglądarka przy otwarciu pliku z dysku
    # zgaduje kodowanie z pierwszego fragmentu i czasem czyta UTF-8 jako Latin-1 (błąd skryptu „Range out of order”, przebieg r32)
    s = '<meta charset="utf-8">\n' + s
if STYL not in s:
    i = s.find('</title>') + len('</title>'); assert i > 8 and i < 400, 'STOP 11zz11: brak tytułu na początku kursu'
    s = s[:i] + STYL + s[i:]
assert s.count(STYL) == 1 and s.find(STYL) < 400, 'STOP 11zz11: styl objaśnień poza początkiem strony'
if s != s0: open(P, 'w', encoding='utf-8').write(s)
if len(sys.argv) <= 1:
    c = sqlite3.connect(os.environ.get('BHP_DB', f'{B}/bhp_rejestr.sqlite'))
    c.execute('begin')   # usunięcie, odtworzenie i wypełnienie tabeli oraz widoku w jednej transakcji (uwaga Copilota do PR #17)
    c.execute('drop view if exists v_obraz_objasnienie'); c.execute('drop table if exists obraz_objasnienie')
    c.execute('''create table obraz_objasnienie(sekcja text, ident text, ma_dobrze_zle_widoczne integer, zrodlo text, stan text,
                 sha256_obrazu text, podpis text, dobrze text, zle text, dlaczego text, jak_postepowac text, primary key(sekcja, ident))''')
    c.executemany("insert or replace into obraz_objasnienie values(?,?,?,?,?,?,?,?,?,?,?)",
                  [(r_[0], r_[1], r_[2], r_[3], 'OBJAŚNIONA' if r_[2] and not (r_[7] and not r_[8]) else
                    ('DO OPRACOWANIA – brak „dlaczego”' if r_[2] else 'DO OPRACOWANIA')) + r_[4:] for r_ in rej])
    # widok dla innych silników: objaśnienie + plik oryginału i oznaczenie rysunku z rejestru obrazów (klucz: skrót obrazu w kursie)
    c.execute('''create view v_obraz_objasnienie as select o.sekcja, o.ident, u.ident as ident_rysunku, u.plik_zrodlowy, o.sha256_obrazu,
                 o.podpis, o.dobrze, o.zle, o.dlaczego, o.jak_postepowac, o.zrodlo, o.stan
                 from obraz_objasnienie o left join (select distinct ident, plik_zrodlowy, sha256_w_stronie from obraz_uzycie where strona like 'kurs%') u
                 on u.sha256_w_stronie = o.sha256_obrazu''')
    c.execute("update decyzja_ts set wdrozenie='krok 11zz11 build_objasnienia_rysunkow_1116.py (dobrze/źle z treści planszy do podpisu; tabela obraz_objasnienie); kontrola D-150' where id=150")
    c.commit(); c.close()
print(f'11zz11 objaśnienia rysunków: dopiski usunięte {n1 + n1b} | dobrze/źle dodane {n2} | „do przeglądu” usunięte {n3} | m12 przeniesiony {n4} '
      f'| z tabeli objaśnień {n5} | instrukcje {n6} | „dlaczego” dopisane {n7} | podpisy Właściwie/Niewłaściwie {n8} | plansze w modułach {len(rej)}, z widocznym dobrze/źle {sum(r[2] for r in rej)}')

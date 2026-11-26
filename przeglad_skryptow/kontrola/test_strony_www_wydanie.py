# Test wyniku na ZŁOŻONYCH stronach www (dec. TS 186, 18.11.2026 17:42): po kroku 6 wydania, na plikach w REPO_WWW.
# Powód: PR #26 wyszedł ze starymi skrótami PIN-ów, bo kontrole badały źródło, a nie to, co idzie na stronę.
# Użycie: HASLO_WWW=... HASLO_WWW_PRAC=... python3 test_strony_www_wydanie.py <REPO_WWW>
# Sprawdza (wszystko względem bazy bhp_rejestr, bez LLM):
#  W-01 skrót hasła /pelny/ i /pracownik/ = www_ustawienie; strona daje się odszyfrować tym hasłem
#  W-02 skróty PIN-ów na stronie = v_www_pin_aktualny (każda osoba ze strony, żadnej osoby bez PIN-u)
#  W-03 role na stronie = rola_www (PODGLAD tylko na /pelny/; /pracownik/ tylko pracownicy CURL)
#  W-04 zapis.json /pelny/ i /pracownik/ = ZAPIS_URL_PELNY_PRACOWNIK; publiczny = ZAPIS_URL_PUBLICZNY
#  W-05 w przeglądarce: dobre hasło otwiera logowanie, zły PIN jest odrzucony, złe hasło jest odrzucone
#  W-06 brak jawnych haseł w plikach strony
#  N-01 test negatywny: porównanie W-02/W-03 wykrywa celowo zepsuty skrót i rolę
#  W-07 (ZG-1119-1531-1, TS 19.11): w publikowanych plikach (wszystko poza .git, .github, tests/, README.md – tak samo jak
#       w .github/workflows/strona.yml) nie ma żadnego jawnego PDF ani innego jawnego pliku; dozwolone są tylko: strona publiczna
#       index.html (bez sekcji treści), zapis.json, .nojekyll, zaszyfrowane index.html stron /pelny/, /pracownik/, /pelny/aplikacja/
#       i zaszyfrowane karty charakterystyki <strona>/sds/*.bin
#  W-08 (usterka A, 21.11.2026; od 22.11 każdy plik */pracownik/index.html w repozytorium): odszyfrowana strona /pracownik/ (wspólne hasło) ma 0 rekordów osobowych: puste KARTAOS i DOKPOD,
#       żadnego osadzonego PDF; N-03 test negatywny: podłożony rekord KARTAOS, dopisana osoba DOKPOD i osadzony PDF są wykryte
#  N-02 test negatywny: W-07 wykrywa podłożony jawny PDF, jawny PDF udający .bin, dowiązanie symboliczne do PDF i jawną stronę z treścią
# Wynik: wiersze w polecenie_kontrola_wynik (polecenie D-186, nr 0); kod ≠ 0 = STOP wydania.
import os, sys, re, json, base64, hashlib, sqlite3, subprocess, datetime, tempfile
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
B = '/mnt/project-files/bhp'
REPO = sys.argv[1]
H = {'pelny': os.environ['HASLO_WWW'], 'pracownik': os.environ['HASLO_WWW_PRAC']}
db = sqlite3.connect(f'{B}/bhp_rejestr.sqlite')
UST = dict(db.execute('select klucz, wartosc from v_www_ustawienie_aktualne'))
PIN = dict(db.execute('select kod, sha from v_www_pin_aktualny'))
ROLA = {k: (r, pc) for k, r, pc in db.execute('select kod, rola, pracownik_curl from rola_www')}
wyniki = []
def wynik(kod, ok, opis):
    wyniki.append((kod, bool(ok), opis)); print(('OK   ' if ok else 'BŁĄD ') + kod + ' ' + opis)

def odszyfruj(plik, haslo):
    t = open(plik, encoding='utf8').read()
    m = re.search(r'const D=\{s:"([^"]+)",i:"([^"]+)",n:(\d+),c:"([^"]+)"\}', t)
    assert m, f'{plik}: brak danych szyfrowania'
    s, i, n, c = base64.b64decode(m[1]), base64.b64decode(m[2]), int(m[3]), base64.b64decode(m[4])
    k = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=s, iterations=n).derive(haslo.encode())
    return json.loads(AESGCM(k).decrypt(i, c, None))

def porownaj(tryb, login):
    bledy = []
    for kod, sha in login['piny'].items():
        if PIN.get(kod) != sha: bledy.append(f'PIN {kod}: strona ≠ baza')
    for o in login['osoby']:
        if o[0] not in login['piny']: bledy.append(f'PIN {o[0]}: osoba na stronie bez PIN-u')
        r, pc = ROLA.get(o[0], ('PRACOWNIK', 1))
        oczek = 'PRACOWNIK' if tryb == 'pracownik' else (r or 'PRACOWNIK')
        if o[3] != oczek: bledy.append(f'rola {o[0]}: strona {o[3]} ≠ baza {oczek}')
        if tryb == 'pracownik' and not o[4]: bledy.append(f'{o[0]}: osoba spoza CURL na stronie pracownika')
    return bledy

for tryb in ('pelny', 'pracownik'):
    klucz = {'pelny': 'HASLO_PELNY_SHA256', 'pracownik': 'HASLO_PRACOWNIK_SHA256'}[tryb]
    wynik(f'W-01 {tryb}', hashlib.sha256(H[tryb].encode()).hexdigest() == UST.get(klucz), f'skrót hasła = www_ustawienie.{klucz}')
    try:
        P = odszyfruj(f'{REPO}/{tryb}/index.html', H[tryb]); wynik(f'W-01 {tryb} odszyfrowanie', True, 'strona otwiera się hasłem')
    except Exception as e:
        wynik(f'W-01 {tryb} odszyfrowanie', False, f'strona nie otwiera się hasłem: {e}'); continue
    b = porownaj(tryb, P['login'])
    wynik(f'W-02/W-03 {tryb}', not b, f"PIN-y i role ({len(P['login']['osoby'])} osób) = baza" + ('' if not b else ': ' + '; '.join(b[:8])))
    # N-01: zepsuty skrót i rola muszą zostać wykryte
    zl = json.loads(json.dumps(P['login']))
    k0 = next(iter(zl['piny'])); zl['piny'][k0] = '0' * 64; zl['osoby'][0][3] = 'XXX'
    wynik(f'N-01 {tryb}', len(porownaj(tryb, zl)) >= 2, 'porównanie wykrywa zepsuty skrót PIN-u i rolę')
    z = json.load(open(f'{REPO}/{tryb}/zapis.json'))
    wynik(f'W-04 {tryb}', z.get('url') == UST.get('ZAPIS_URL_PELNY_PRACOWNIK'), 'zapis.json = www_ustawienie.ZAPIS_URL_PELNY_PRACOWNIK')
z = json.load(open(f'{REPO}/zapis.json'))
wynik('W-04 publiczna', z.get('url', '') == UST.get('ZAPIS_URL_PUBLICZNY', ''), 'zapis.json = www_ustawienie.ZAPIS_URL_PUBLICZNY')
jawne = [p for p in ('index.html', 'pelny/index.html', 'pracownik/index.html', 'pelny/aplikacja/index.html')
         if os.path.exists(f'{REPO}/{p}') and any(h in open(f'{REPO}/{p}', encoding='utf8').read() for h in H.values())]
wynik('W-06', not jawne, 'brak jawnych haseł w plikach strony' + (f': {jawne}' if jawne else ''))

# W-07 / N-02: pliki publikowane (ZG-1119-1531-1)
POMIJANE = {'.git', '.github', 'tests', 'README.md'}
DOZWOLONE = re.compile(r'(?:wersja-\d{4}-\d\d-\d\d/)?(?:(?:pelny|pracownik|pelny/aplikacja)/)?(?:zapis\.json)'
                       r'|\.nojekyll|index\.html|(?:wersja-\d{4}-\d\d-\d\d/)?(?:pelny|pracownik|pelny/aplikacja)/index\.html'
                       r'|(?:wersja-\d{4}-\d\d-\d\d/)?(?:pelny|pracownik)/sds/[A-Za-z0-9_.-]+\.bin'
                       r'|przypomnienia/[a-z_]+/index\.html')  # strony przypomnień obszarów (TS 24.11.2026), zaszyfrowane – sprawdza W-07 i W-08p
def nieszyfrowane(repo):
    b = []
    for kat, podk, pliki in os.walk(repo):
        wzg = os.path.relpath(kat, repo)
        if wzg == '.':
            podk[:] = [d for d in podk if d not in POMIJANE]; pliki = [f for f in pliki if f not in POMIJANE]
        for d in podk:  # dowiązanie do katalogu: publikacja by je rozwinęła (uwaga przeglądu #31)
            if os.path.islink(os.path.join(kat, d)): b.append(f'{os.path.normpath(os.path.join(wzg, d))}: dowiązanie symboliczne')
        for f in pliki:
            rel = os.path.normpath(os.path.join(wzg, f)).replace(os.sep, '/')
            if os.path.islink(os.path.join(kat, f)):
                b.append(f'{rel}: dowiązanie symboliczne'); continue
            dane = open(os.path.join(kat, f), 'rb').read()
            if not DOZWOLONE.fullmatch(rel):
                b.append(f'{rel}: plik spoza listy dozwolonych'); continue
            if dane[:5] == b'%PDF-' or b'%PDF-' in dane[:1024]:
                b.append(f'{rel}: jawny PDF'); continue
            if rel.endswith('index.html'):
                t = dane.decode('utf8', 'replace')
                if rel == 'index.html':
                    if '<section' in t: b.append(f'{rel}: strona publiczna z sekcją treści')
                elif not re.search(r'const D=\{(?:s:"[^"]+",i:"[^"]+",n:\d+,c:"[^"]+"\}|"s": "[^"]+", "n": \d+, "p": \{)', t) or '<section' in t:
                    b.append(f'{rel}: strona niezaszyfrowana')
    return b
w7 = nieszyfrowane(REPO)
wynik('W-07', not w7, 'publikowane są tylko strona publiczna, zapis.json i pliki zaszyfrowane' + (': ' + '; '.join(w7[:8]) if w7 else ''))
with tempfile.TemporaryDirectory() as T:
    for rel, d in (('index.html', b'<html></html>'), ('pelny/index.html', b'const D={s:"a",i:"b",n:1,c:"c"}'),
                   ('sds/01_x.pdf', b'%PDF-1.4 x'), ('pelny/sds/02_y.bin', b'%PDF-1.4 y'),
                   ('wersja-2026-11-18/index.html', b'<section id="test">'), ('tests/a.pdf', b'%PDF-1.4 pomijany')):
        os.makedirs(os.path.dirname(f'{T}/{rel}') or T, exist_ok=True); open(f'{T}/{rel}', 'wb').write(d)
    os.symlink(f'{T}/sds/01_x.pdf', f'{T}/pelny/sds/03_z.pdf.bin')
    n2 = nieszyfrowane(T)
    wynik('N-02', len(n2) == 4 and all(any(x.startswith(r) for x in n2) for r in ('sds/01_x.pdf', 'pelny/sds/02_y.bin', 'pelny/sds/03_z.pdf.bin', 'wersja-2026-11-18/index.html')),
          f'test negatywny W-07 wykrywa podłożone jawne pliki: {n2}')

# W-05: zachowanie w przeglądarce
JS = r'''const {chromium}=require('playwright');
(async()=>{const [repo,hp]=process.argv.slice(2);const b=await chromium.launch();const r={};
 let p=await b.newPage();await p.goto('file://'+repo+'/pelny/index.html');await p.fill('#h','zle-haslo-'+Date.now());await p.click('button');await p.waitForTimeout(4000);
 r.zle_haslo_odrzucone=(await p.textContent('#st')).includes('Nieprawidłowe hasło')&&!(await p.$('#n'));await p.close();
 p=await b.newPage();await p.goto('file://'+repo+'/pelny/index.html');await p.fill('#h',hp);await p.click('button');await p.waitForSelector('#n',{timeout:20000});
 r.haslo_otwiera=true;await p.fill('#n','Stuczy');await p.waitForTimeout(300);await p.locator('#pod button').first().click();
 await p.fill('#p','X'+Date.now());await p.click('#z');await p.waitForTimeout(800);
 r.zly_pin_odrzucony=(await p.textContent('#st2')).includes('Nieprawidłowy PIN')&&!!(await p.$('#p'));
 console.log(JSON.stringify(r));await b.close();})().catch(e=>{console.log(JSON.stringify({blad:String(e)}));process.exit(1)});'''
with tempfile.TemporaryDirectory() as T:
    open(f'{T}/t.js', 'w').write(JS)
    pr = subprocess.run(['node', f'{T}/t.js', os.path.abspath(REPO), H['pelny']], capture_output=True, text=True, timeout=300,
                        cwd='/tmp', env=dict(os.environ, NODE_PATH=subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip()))
try:
    r = json.loads(pr.stdout.strip().splitlines()[-1])
except Exception:
    r = {'blad': (pr.stdout + pr.stderr)[-300:]}
for k in ('zle_haslo_odrzucone', 'haslo_otwiera', 'zly_pin_odrzucony'):
    wynik(f'W-05 {k}', r.get(k) is True, f'przeglądarka: {k}' + (f" ({r.get('blad')})" if 'blad' in r else ''))

# W-08 / N-03 (usterka A, 21.11.2026): wersja pracownika bez rekordów osobowych
sys.path.insert(0, f'{B}/skrypty')
from www_bez_danych_osobowych import rekordy_osobowe
try:
    _dp = odszyfruj(f'{REPO}/pracownik/index.html', H['pracownik'])['doc']
    # od 22.11.2026 (kontrola całości): KAŻDY plik */pracownik/index.html w repozytorium (także dawne wersje, np. wersja-2026-11-18/),
    # bo każdy jest publikowany pod wspólnym hasłem pracowników; plik, którego nie da się sprawdzić, też daje STOP
    _r8 = []
    _pliki8 = sorted(os.path.relpath(os.path.join(d, 'index.html'), REPO) for d, ds, fs in os.walk(REPO)
                     if '.git' not in os.path.relpath(d, REPO).split(os.sep) and os.path.basename(d) == 'pracownik' and 'index.html' in fs)
    for _p8 in _pliki8:
        try: _r = rekordy_osobowe(odszyfruj(f'{REPO}/{_p8}', H['pracownik'])['doc'])
        except Exception as e: _r = [f'nie da się sprawdzić ({type(e).__name__})']
        _r8 += [f'{_p8}: {x}' for x in _r]
    wynik('W-08', bool(_pliki8) and not _r8, f'strony */pracownik/ ({len(_pliki8)}: {", ".join(_pliki8)}) bez rekordów osobowych (KARTAOS, DOKPOD, osadzone PDF, kategorie zaszeregowania)' + (': ' + '; '.join(_r8) if _r8 else ''))
    _zepsute = [re.sub(r'(window\.KARTAOS=\{"dzis":"[0-9-]+","osoby":)\{\}', r'\1{"XX":{"dk":[]}}', _dp, count=1),
                _dp + '<script>Object.assign(window.DOKPOD.osoby,{"XX":{"n":"Test"}});</script>',
                _dp + '<script>var p="JVBERi0xLjQK";</script>',
                _dp + '<script>var st={"XX":"technik (IV kat. zaszeregowania)"};</script>']
    _n3 = [bool(rekordy_osobowe(z)) for z in _zepsute]
    wynik('N-03', all(_n3) and 'window.KARTAOS={' in _dp, f'test negatywny W-08 wykrywa rekord KARTAOS, osobę DOKPOD, PDF i kategorię zaszeregowania: {_n3}')
except Exception as e:
    wynik('W-08', False, f'nie sprawdzono strony /pracownik/: {e}')

# W-08p (TS 24.11.2026, strony przypomnień obszarów): każdy plik przypomnienia/*/index.html otwiera się hasłem swojego obszaru (HASLA_PRZYP)
# i nie zawiera danych osobowych z kart ani płac; liczba stron = liczba haseł; plik, którego nie da się sprawdzić, daje STOP
_hp = json.loads(os.environ.get('HASLA_PRZYP') or '{}')
_sl = {re.sub(r'^S_', '', k).lower(): v for k, v in _hp.items()}
_pp = sorted(d for d in (os.listdir(f'{REPO}/przypomnienia') if os.path.isdir(f'{REPO}/przypomnienia') else []))
_rp = []
for _d in _pp:
    try:
        _doc = odszyfruj(f'{REPO}/przypomnienia/{_d}/index.html', _sl[_d])['doc']
        _rp += [f'{_d}: {x}' for x in rekordy_osobowe(_doc)]
        _rp += [f'{_d}: {m}' for m in sorted(set(re.findall(r'(?i)KARTAOS|DOKPOD|PESEL|wynagrodz\w*|zaszeregowan\w*', _doc)))]
    except Exception as e: _rp.append(f'{_d}: nie da się sprawdzić ({type(e).__name__})')
wynik('W-08p', (not _pp and not _hp) or (sorted(_sl) == _pp and not _rp),
      f'strony przypomnień ({len(_pp)}: {", ".join(_pp)}; haseł {len(_hp)}) zaszyfrowane hasłem obszaru, bez danych osobowych i płac' + (': ' + '; '.join(_rp) if _rp else ''))

czas = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
sha = hashlib.sha256(open(f'{REPO}/pelny/index.html', 'rb').read()).hexdigest()
db.executemany('insert into polecenie_kontrola_wynik values(?,?,?,?,?,?,?)',
               [(czas, sha, 'D-186', 0, kod + ' (strony www w ' + REPO + ')', opis[:300], int(ok)) for kod, ok, opis in wyniki])
db.commit()
zle = [w for w in wyniki if not w[1]]
print(f'test stron www: {len(wyniki)} sprawdzeń, błędów {len(zle)}')
sys.exit(1 if zle else 0)

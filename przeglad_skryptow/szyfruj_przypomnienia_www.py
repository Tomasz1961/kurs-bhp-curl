#!/usr/bin/env python3
"""Krok 6 wydania (24.11.2026, TS 24.11 15:50/15:55): strony „Przypomnienia” dla obszarów – szyfrowanie i publikacja pod /przypomnienia/<obszar>/.
Treść (NIEZASZYFROWANY HTML <katalog>/<OBSZAR>/index.html) buduje część KADRY: adm/skrypty/build_przypomnienia_www.py z bazy aplikacji.
Ten skrypt tylko szyfruje każdą stronę hasłem jej obszaru (AES-256-GCM, klucz z hasła przez PBKDF2-SHA256, 600 000 iteracji – ta sama metoda
co /pelny/ i /pracownik/) i zapisuje <REPO_WWW>/przypomnienia/<obszar>/index.html. Wejście tylko ze zmiennych: PRZYPOMNIENIA_JAWNE (krok 6p), REPO_WWW, HASLA_PRZYP (JSON {OBSZAR: hasło}),
nigdy w pliku repozytorium ani na Dysku.
Reguły (STOP, kod ≠ 0):
  PR-01 zbiór obszarów w katalogu = zbiór haseł = zbiór kluczy HASLO_PRZYP_<OBSZAR>_SHA256 w ADM (ustawienie_aktualne);
  PR-02 sha256(hasło) = wartość w ADM dla każdego obszaru;
  PR-03 treść bez danych osobowych z kart i bez płac (KARTAOS, DOKPOD, PESEL, wynagrodzenie, zaszeregowanie, stawka, osadzony PDF);
  PR-04 hasło obszaru ≠ hasło /pelny/ i /pracownik/, hasła obszarów różne między sobą, co najmniej 12 znaków.
Testy negatywne w każdym przebiegu: podłożony zły skrót, płaca w treści i powtórzone hasło są wykryte. Bez LLM."""
import os, sys, re, json, base64, hashlib, sqlite3, shutil
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ADM = '/mnt/project-files/adm/adm.sqlite'
ITER = 600_000
ZAKAZ = re.compile(r'KARTAOS|DOKPOD|PESEL|wynagrodz|zaszeregowan|\bstawk\w*|zł\s*/\s*(?:h|godz)|JVBERi0', re.I)  # uwaga przeglądu #44: każda stawka, nie tylko godzinowa

def adm_skroty(adm=ADM):
    c = sqlite3.connect(f'file:{adm}?mode=ro', uri=True)
    r = {k[len('HASLO_PRZYP_'):-len('_SHA256')]: v for k, v in
         c.execute("select klucz, wartosc from ustawienie_aktualne where klucz like 'HASLO\\_PRZYP\\_%\\_SHA256' escape '\\'")}
    c.close(); return r

def kontrola(obszary, hasla, skroty, tresci, inne_hasla):
    W = []
    if not (set(obszary) == set(hasla) == set(skroty)):
        W.append(f'PR-01 obszary: katalog {sorted(obszary)} / hasła {sorted(hasla)} / ADM {sorted(skroty)}')
    for ob in sorted(set(hasla) & set(skroty)):
        if hashlib.sha256(hasla[ob].encode()).hexdigest() != skroty[ob]: W.append(f'PR-02 {ob}: skrót hasła ≠ ADM')
    for ob, t in sorted(tresci.items()):
        z = sorted(set(m.group(0) for m in ZAKAZ.finditer(t)))
        if z: W.append(f'PR-03 {ob}: zakazana treść {z}')
    hs = list(hasla.values())
    if len(set(hs)) != len(hs): W.append('PR-04 powtórzone hasło obszaru')
    if any(len(h) < 12 for h in hs): W.append('PR-04 hasło krótsze niż 12 znaków')
    if set(hs) & set(x for x in inne_hasla if x): W.append('PR-04 hasło obszaru równe hasłu /pelny/ albo /pracownik/')
    return W

def test_negatywny(obszary, hasla, skroty, tresci, inne):
    # uwaga przeglądu #44: każdy podłożony błąd musi dać SWOJĄ regułę (a nie dowolny błąd)
    ob, ob2 = sorted(obszary)[:2]
    ma = lambda W, r: any(w.startswith(r) for w in W)
    zly = dict(skroty); zly[ob] = '0' * 64
    pl = dict(tresci); pl[ob] = pl[ob] + '<p>Stawka zasadnicza: 5000 zł</p>'
    pw = dict(hasla); pw[ob2] = pw[ob]
    sk2 = dict(skroty); sk2[ob2] = hashlib.sha256(pw[ob2].encode()).hexdigest()   # skrót zgodny, żeby PR-02 nie zasłonił PR-04
    return [ma(kontrola(obszary, hasla, zly, tresci, inne), 'PR-02'), ma(kontrola(obszary, hasla, skroty, pl, inne), 'PR-03'),
            ma(kontrola(obszary, pw, sk2, tresci, inne), 'PR-04 powtórzone')]

LOADER = '''<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Przypomnienia</title>
<style>body{font-family:system-ui,sans-serif;background:#f4f4f2;color:#1b1b1b;margin:0;display:flex;min-height:100vh;align-items:center;justify-content:center}
.box{background:#fff;border:1px solid #ddd;border-radius:12px;padding:24px;max-width:420px;width:calc(100% - 32px);box-sizing:border-box}h1{font-size:20px;margin:0 0 8px}p{font-size:14px;color:#555}
input,button{font-size:16px;padding:10px;border-radius:8px;border:1px solid #bbb;width:100%;box-sizing:border-box;margin-top:8px;min-height:48px}button{background:#14532d;color:#fff;border:0;cursor:pointer}#st{min-height:1.4em;color:#b91c1c}</style></head>
<body><form class="box" id="f"><h1>Przypomnienia</h1><p>Strona dla osób upoważnionych. Wpisz hasło otrzymane od administratora.</p>
<input id="h" type="password" autocomplete="current-password" placeholder="Hasło" autofocus><button>Otwórz</button><p id="st" role="status" aria-live="polite"></p></form>
<script>(()=>{const D={s:"__S__",i:"__I__",n:__N__,c:"__C__"};const u=b=>Uint8Array.from(atob(b),c=>c.charCodeAt(0));
document.getElementById("f").addEventListener("submit",async e=>{e.preventDefault();const st=document.getElementById("st");st.style.color="#555";st.textContent="Otwieranie…";
 try{const k0=await crypto.subtle.importKey("raw",new TextEncoder().encode(document.getElementById("h").value),"PBKDF2",false,["deriveKey"]);
  const k=await crypto.subtle.deriveKey({name:"PBKDF2",salt:u(D.s),iterations:D.n,hash:"SHA-256"},k0,{name:"AES-GCM",length:256},false,["decrypt"]);
  const P=JSON.parse(new TextDecoder().decode(await crypto.subtle.decrypt({name:"AES-GCM",iv:u(D.i)},k,u(D.c))));
  document.open();document.write(P.doc);document.close();}
 catch(x){st.style.color="#b91c1c";st.textContent="Nieprawidłowe hasło.";}});})();</script></body></html>
'''

def szyfruj(doc, haslo):
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(haslo.encode())
    ct = AESGCM(key).encrypt(iv, json.dumps({'doc': doc}, ensure_ascii=False).encode('utf8'), None)
    b = lambda x: base64.b64encode(x).decode()
    return LOADER.replace('__S__', b(salt)).replace('__I__', b(iv)).replace('__N__', str(ITER)).replace('__C__', b(ct))

def slug(ob): return re.sub(r'^S_', '', ob).lower()

def main():
    jaw = os.environ.get('PRZYPOMNIENIA_JAWNE') or sys.exit('STOP PR-01: brak PRZYPOMNIENIA_JAWNE (katalog z kroku 6p)')
    repo = os.environ.get('REPO_WWW') or sys.exit('STOP PR-01: brak REPO_WWW')
    _j, _r = os.path.realpath(jaw), os.path.realpath(repo)   # uwaga przeglądu #44: także ten sam katalog (i przez dowiązanie)
    if _j == _r or _j.startswith(_r + os.sep): sys.exit('STOP PR-01: treść jawna w REPO_WWW')
    hasla = json.loads(os.environ.get('HASLA_PRZYP') or sys.exit('STOP PR-01: brak HASLA_PRZYP'))
    obszary = sorted(d for d in os.listdir(jaw) if os.path.isfile(os.path.join(jaw, d, 'index.html')))
    tresci = {ob: open(os.path.join(jaw, ob, 'index.html'), encoding='utf-8').read() for ob in obszary}
    skroty = adm_skroty()
    inne = (os.environ.get('HASLO_WWW', ''), os.environ.get('HASLO_WWW_PRAC', ''))
    W = kontrola(obszary, hasla, skroty, tresci, inne)
    neg = test_negatywny(obszary, hasla, skroty, tresci, inne) if len(obszary) >= 2 else [False]
    if not all(neg): W.append(f'test negatywny nie wykrył zmiany: {neg}')
    if W:
        print('STOP przypomnienia:\n  ' + '\n  '.join(W)); sys.exit(1)
    cel = os.path.join(repo, 'przypomnienia')
    if os.path.isdir(cel): shutil.rmtree(cel)
    for ob in obszary:
        os.makedirs(os.path.join(cel, slug(ob)), exist_ok=True)
        open(os.path.join(cel, slug(ob), 'index.html'), 'w', encoding='utf-8').write(szyfruj(tresci[ob], hasla[ob]))
    print(f'przypomnienia: {len(obszary)} stron zaszyfrowanych → {cel} ({", ".join(slug(o) for o in obszary)}) | testy negatywne {sum(neg)}/{len(neg)}')

if __name__ == '__main__':
    main()

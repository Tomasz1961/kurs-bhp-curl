# Pełna wersja kursu na www dla J. Grzegórskiej (prośba TS 13.11.2026 11:45: „Chcę pełne na www też dla Grzegórskiej”).
# Repozytorium Pages jest publiczne, a pełna wersja zawiera nazwiska pracowników (lista uczestników, listy podpisów kart),
# więc plik jest SZYFROWANY: AES-256-GCM, klucz z hasła przez PBKDF2-SHA256 (600 000 iteracji). Bez hasła treść jest nieczytelna.
# Hasło podaje się w zmiennej środowiskowej HASLO_WWW; nie jest zapisywane w repozytorium, w git ani na Dysku.
# Użycie: HASLO_WWW=... [TRYB_WWW=pelny|pracownik] python3 build_wersja_www_pelna.py <katalog_wyjściowy>
# TS 16.11.2026 14:56 UTC: osobne hasło dla pracowników (strona /pracownik/: tylko pracownicy CURL, każdy widzi tylko siebie,
# bez danych podglądu) i osobne dla pełnego dostępu (strona /pelny/: osoby z podglądem); „Administrator”, nie „Kierownik Centrum”;
# J. Grzegórska (nie pracuje w CURL, pracownik_curl=0) nie ma „Mój test i moje dokumenty”.
import os, sys, base64, hashlib, subprocess, json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
B = '/mnt/project-files/bhp'
OUT = sys.argv[1]
haslo = os.environ['HASLO_WWW']
TRYB = os.environ.get('TRYB_WWW', 'pelny'); assert TRYB in ('pelny', 'pracownik'), TRYB
assert len(haslo) >= 12
tmp = f'{OUT}/.pelny_tmp.html'
subprocess.run([sys.executable, f'{B}/skrypty/kopia_samodzielna.py', tmp], check=True, stdout=subprocess.DEVNULL)
doc = open(tmp, encoding='utf8').read(); os.remove(tmp)
# czcionki Google wyłączone (bez połączeń do Google), reszta bez zmian
doc = doc.replace('<link rel="preconnect" href="https://fonts.googleapis.com">', '')
import re
doc = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^"]*"[^>]*>', '', doc)
# C-04 (audyt 15.11.2026): karty charakterystyki leżą w repozytorium w sds/ (wspólne dla obu wersji), a strona pełna jest w /pelny/
n_sds = doc.count('href="sds/'); assert n_sds >= 20, n_sds
doc = doc.replace('href="sds/', 'href="../sds/')
# ── OBIEKT (TS 16.11.2026 14:56–14:57 UTC „jedna aplikacja … pomieszczenie jest jak szuflada”; TS-2026-11-16-09/02) ─────────────
# Zakładki „Plan obiektu”, „Pomieszczenia”, „Środki ochrony w strefach” z fragmentów wątku systemu BHP (system_bhp.sqlite, jedna baza),
# tylko na stronie /pelny/ (plan obiektu). Przed wstawieniem: sha256 i wielkość każdego pliku = MANIFEST.json, a każdy obraz
# w fragmencie musi być DOPUSZCZONY w rejestrze obrazów kursu (D-134). Niezgodność = STOP budowy strony.
if TRYB == 'pelny':
    _DA = f'{B}/system/do_aplikacji'
    _man = json.load(open(f'{_DA}/MANIFEST.json', encoding='utf8'))
    import sqlite3 as _sq2
    _rej = _sq2.connect(f'file:{B}/bhp_rejestr.sqlite?mode=ro', uri=True)
    _ZAK = [('mapa', 'obiekt_plan', 'Plan obiektu', 'Plan obiektu i drogi'), ('pomieszczenia', 'obiekt_pomieszczenia', 'Pomieszczenia', 'Pomieszczenia: czynności, wymagania stanowisk, instrukcje'),
            ('srodki', 'obiekt_srodki', 'Środki ochrony w strefach', 'Odzież i środki ochrony indywidualnej w strefach')]
    _pl = {x['fragment']: x for x in _man['pliki']}
    assert set(_pl) == {z[0] for z in _ZAK}, sorted(_pl)
    _sekcje = ''
    for _fr, _id, _tyt, _nagl in _ZAK:
        _raw = open(f"{_DA}/{_pl[_fr]['plik']}", 'rb').read()
        assert hashlib.sha256(_raw).hexdigest() == _pl[_fr]['sha256'] and len(_raw) == _pl[_fr]['bajtow'], f'STOP: fragment {_fr} niezgodny z MANIFEST'
        _t = _raw.decode('utf8')
        # dec. TS 146 (opis planu bez dopisków wewnętrznych) i 153 (bez list braków dla działu BHP) – STOP budowy strony
        _zak = re.findall(r'zmniejszon|zatwierdzon\w* przez|Braki w rejestrze|brak karty – do uzupełnienia', _t)
        assert not _zak, f'STOP D-146/D-153: fragment {_fr} zawiera {sorted(set(_zak))}'
        for _b64 in re.findall(r'src="data:image/[a-z+]+;base64,([^"]+)"', _t):
            _sh = hashlib.sha256(base64.b64decode(_b64)).hexdigest()
            assert _rej.execute("select count(*) from obraz_uzycie where sha256_w_stronie=? and stan='DOPUSZCZONY' and strona like 'kurs%'", (_sh,)).fetchone()[0] >= 1, f'STOP D-134: obraz {_sh[:12]} w fragmencie {_fr} nie jest dopuszczony w kursie'
        assert not re.search(r'<img[^>]+src="(?!data:)', _t), f'STOP: obraz spoza fragmentu w {_fr}'
        _sekcje += (f'<section id="{_id}" data-title="{_tyt}" data-sign="info" data-sbhp-fragment="{_fr}" data-sbhp-sha="{_pl[_fr]["sha256"]}">'
                    f'<div class="mhead"><span class="sign info"></span><div><div class="eyebrow">Obiekt</div><h2>{_nagl}</h2></div></div>{_t}</section>\n')
    _MAPF = {z[0]: z[1] for z in _ZAK}
    _sekcje += ('<script>(function(){var M=' + json.dumps(_MAPF) + ';document.addEventListener("sbhp-pokaz",function(e){var id=M[(e.detail||{}).fragment];'
                'if(!id)return;history.pushState(null,"","#"+id);if(typeof route==="function")route()})})();</script>\n')
    assert doc.count('<section id="dokumenty"') == 1
    doc = doc.replace('<section id="dokumenty"', _sekcje + '<section id="dokumenty"', 1)
    _nv = 'if(s.id==="kartyryzyka"){const d=document.createElement("div");d.className="navsep";d.textContent="Karty";nav.appendChild(d)}'
    assert doc.count(_nv) == 1
    doc = doc.replace(_nv, _nv + 'if(s.id==="obiekt_plan"){const d=document.createElement("div");d.className="navsep";d.textContent="Obiekt";nav.appendChild(d)}', 1)
doc, n_wz = re.subn(r' · <a href="wzory/[^"]+">kopia lokalna \(folder wzory\)</a>', '', doc)
assert n_wz == 2, f'wzory wniosków: {n_wz}'
assert not re.search(r'href="(?!https?:|mailto:|#|\.\./sds/|data:|javascript:)[^"]+\.(pdf|docx|xlsx|html)"', doc), 'odnośnik względny do pliku, którego nie ma w repozytorium'
# ── WWW-LOGOWANIE (TS 15.11.2026 22:42–22:44, karta „Na www, własny login z PIN”) ─────────────────────────────────────
# Po haśle strony: wpisanie nazwiska (podpowiedź także bez polskich znaków, bez listy nazwisk na pierwszej stronie) i PIN-u.
# PIN sprawdzany skrótem sha256("CURL-PIN|KOD|PIN") – ten sam co w kursie; skróty z piny/aktualne (PINY_WWW, plik spoza repozytorium).
# Rola z bhp_rejestr.rola_www: PODGLAD = widzi wszystko bez zmian (te same zakładki co prowadzący, w trybie podglądu kursu)
# albo „mój test” jak pracownik; pozostali = pracownik (wynik zapisuje się z jego kodem i PIN-em, bez ponownego pytania).
# Dane prowadzącego dla podglądu: kurs_admin_dane.json + sprawy do załatwienia (ALERTY_WWW) – tylko wewnątrz szyfrowanej treści.
import sqlite3 as _sq
_db = _sq.connect(f'file:{B}/bhp_rejestr.sqlite?mode=ro', uri=True)
_ROLA = {k: (n, f, r, pc) for k, n, f, r, pc in _db.execute('select kod, imie_nazwisko, funkcja, rola, pracownik_curl from rola_www')}
_PEOPLE = json.loads(re.search(r'const PEOPLE=(\[\[.*?\]\]);', doc).group(1))
_nadz = json.loads(re.search(r'window\.OSOBY_NADZORU=(\[.*?\]);', doc).group(1))
_osoby = [[k, n, _ROLA.get(k, (0, '', '', 1))[1], _ROLA.get(k, (0, '', '', 1))[2] or 'PRACOWNIK', _ROLA.get(k, (0, '', '', 1))[3]] for k, n in _PEOPLE + _nadz]
if TRYB == 'pracownik':   # tylko pracownicy CURL, każdy jako pracownik (bez podglądu innych)
    _osoby = [[k, n, f, 'PRACOWNIK', pc] for k, n, f, r, pc in _osoby if pc]
_pj = json.load(open(os.environ['PINY_WWW'], encoding='utf8')); _pj = _pj.get('data', _pj)
_piny = {k: v['sha'] for k, v in _pj.items() if isinstance(v, dict) and re.fullmatch(r'[0-9a-f]{64}', str(v.get('sha', '')))}
_piny = {k: v for k, v in _piny.items() if k in {o[0] for o in _osoby}}
assert len(_piny) >= 10, 'za mało PIN-ów do logowania na www'
_dane = json.load(open(f'{B}/kurs_online/kurs_admin_dane.json', encoding='utf8'))
# dec. TS 153: listy braków nie trafiają na stronę www (podgląd p. Grzegórskiej) – w danych osób pole „braki” puste (uwaga Copilota do PR #16)
_pd = _dane.get('prac-data'); _pds = isinstance(_pd, str); _pd = json.loads(_pd) if _pds else _pd
if _pd:
    for _o in _pd.get('ludzie', []): _o['braki'] = []
    _dane['prac-data'] = json.dumps(_pd, ensure_ascii=False) if _pds else _pd
assert not os.environ.get('ALERTY_WWW'), 'STOP D-153: sprawy do załatwienia (braki) nie idą na stronę www'
_rek = [{'kol': 'kurs_admin', 'id': 'dane', 'd': _dane}]
if os.environ.get('ALERTY_WWW'):
    _al = json.load(open(os.environ['ALERTY_WWW'], encoding='utf8')); _al = _al.get('data', _al)
    _rek.append({'kol': 'kurs_admin', 'id': 'alerty', 'd': _al})
import datetime as _dt
LOGIN = {'osoby': _osoby, 'piny': _piny, 'podglad': {'rek': _rek, 'odswiezono': _dt.datetime.utcnow().isoformat() + 'Z'}}
if TRYB == 'pracownik': LOGIN['podglad'] = {'rek': [], 'odswiezono': ''}
assert TRYB == 'pelny' or not any(o[3] == 'PODGLAD' for o in _osoby), 'strona pracownika z rolą podglądu'
SHIM_PODGLAD = r"""<script>/*WWW-PODGLAD*/(function(){const L=window.WWW_LOGIN;if(!L||L.tryb!=="podglad")return;const id="www-"+L.kod;
const M={};const put=(c,i,v)=>{(M[c]=M[c]||{})[i]=v};
put("podglad",id,{format:"podglad-2",gen:"w",czesci:1,epoka:1,odswiezono:L.odswiezono});put("podglad/"+id+"/k","w_c000",{rek:L.rek});M["podglad/"+id+"/odwolanie"]={};
const snap=(i,v)=>({id:i,exists:v!=null,data:()=>v==null?undefined:v,metadata:{fromCache:false,hasPendingWrites:false}});
function kol(n){M[n]=M[n]||{};const q={id:n.split("/").pop(),path:n,where:()=>q,orderBy:()=>q,limit:()=>q,
 doc:i=>({id:i,path:n+"/"+i,get:async()=>snap(i,M[n][i]),set:async v=>{M[n][i]=v},update:async v=>{M[n][i]=Object.assign({},M[n][i],v)},delete:async()=>{delete M[n][i]},onSnapshot:f=>{f(snap(i,M[n][i]));return()=>{}},collection:c=>kol(n+"/"+i+"/"+c)}),
 add:async v=>{const i="l"+Date.now();M[n][i]=v;return{id:i}},
 get:async()=>{const d=Object.entries(M[n]).map(([k,v])=>snap(k,v));return{docs:d,size:d.length,empty:!d.length,forEach:f=>d.forEach(f),docChanges:()=>[]}},
 onSnapshot:f=>{q.get().then(f);return()=>{}}};return q}
const db={collection:kol,doc:p=>{const a=p.split("/");return kol(a.slice(0,-1).join("/")).doc(a[a.length-1])}};
const user={isOwner:async()=>false,canEdit:async()=>false,can:()=>false,id:async()=>id,me:async()=>({id,name:L.nazwa}),profiles:async()=>({}),search:async()=>[]};
window.claude={use:n=>Promise.resolve(n==="db"?db:n==="user"?user:null)};})();</script>"""
SHIM_PRAC = r"""<script>/*WWW-PRACOWNIK*/(function(){const L=window.WWW_LOGIN;if(!L||L.tryb!=="pracownik")return;
addEventListener("load",()=>{document.querySelectorAll("#who,[data-szkwho]").forEach(w=>{[...w.options].forEach(o=>{if(o.value&&o.value!==L.kod)o.remove()});w.value=L.kod;w.dispatchEvent(new Event("change",{bubbles:true}))})});})();</script>"""
_A = '/*ZAPIS-WWW-PIN*/let kp=null;'
assert doc.count(_A) == 1, 'brak miejsca zapisu wyniku z PIN-em'
doc = doc.replace(_A, '/*ZAPIS-WWW-PIN*/if(window.WWW_LOGIN&&WWW_LOGIN.tryb==="pracownik"&&!rec.pin_skrot)rec=Object.assign({},rec,{kod_osoby:WWW_LOGIN.kod,pin_skrot:WWW_LOGIN.sha});let kp=null;')
_H = '<head><meta charset="utf-8">'
assert 0 <= doc.find(_H) < 200, 'brak nagłówka dokumentu'
doc = doc.replace(_H, _H + '<!--WWW-SHIM-->' + SHIM_PODGLAD + SHIM_PRAC, 1)
payload = json.dumps({'doc': doc, 'login': LOGIN}, ensure_ascii=False)
TYTUL = {'pelny': 'Kurs BHP CURL – pełny dostęp', 'pracownik': 'Kurs BHP CURL – pracownicy'}[TRYB]
OPIS = {'pelny': 'Strona dla administratora i osób z uprawnieniem podglądu (dział BHP, specjaliści ds. jakości). Zawiera dane pracowników, dlatego jest zaszyfrowana.',
        'pracownik': 'Strona dla pracowników CURL: materiały, szkolenie wstępne krok po kroku, test i własne wyniki. Każdy widzi tylko swoje dane.'}[TRYB]
ITER = 600_000
salt, iv = os.urandom(16), os.urandom(12)
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(haslo.encode())
ct = AESGCM(key).encrypt(iv, payload.encode('utf8'), None)
b64 = lambda b: base64.b64encode(b).decode()
loader = '''<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>%s</title>
<style>body{font-family:system-ui,sans-serif;background:#f4f4f2;color:#1b1b1b;margin:0;display:flex;min-height:100vh;align-items:center;justify-content:center}
.pod{background:#eef3ee!important;color:#14532d!important;text-align:left;border:1px solid #cfe0cf!important;margin-top:4px!important}.box{background:#fff;border:1px solid #ddd;border-radius:12px;padding:24px;max-width:420px;width:calc(100%% - 32px)}h1{font-size:20px;margin:0 0 8px}p{font-size:14px;color:#555}
input,button{font-size:16px;padding:10px;border-radius:8px;border:1px solid #bbb;width:100%%;box-sizing:border-box;margin-top:8px}button{background:#14532d;color:#fff;border:0;cursor:pointer}#st{min-height:1.4em;color:#b91c1c}</style></head>
<body><form class="box" id="f"><h1>%s</h1><p>%s Wpisz hasło otrzymane od administratora.</p>
<input id="h" type="password" autocomplete="current-password" placeholder="Hasło" autofocus><button>Otwórz kurs</button><p id="st"></p></form>
<script>(()=>{/* zakres lokalny: document.write zachowuje globalne deklaracje skryptu – nazwy nie mogą kolidować z kursem */
const D={s:"%s",i:"%s",n:%d,c:"%s"};
const u=b=>Uint8Array.from(atob(b),c=>c.charCodeAt(0));
document.getElementById("f").addEventListener("submit",async e=>{e.preventDefault();const st=document.getElementById("st");st.style.color="#555";st.textContent="Otwieranie…";
 try{const k0=await crypto.subtle.importKey("raw",new TextEncoder().encode(document.getElementById("h").value),"PBKDF2",false,["deriveKey"]);
  const k=await crypto.subtle.deriveKey({name:"PBKDF2",salt:u(D.s),iterations:D.n,hash:"SHA-256"},k0,{name:"AES-GCM",length:256},false,["decrypt"]);
  const pt=await crypto.subtle.decrypt({name:"AES-GCM",iv:u(D.i)},k,u(D.c));
  const P=JSON.parse(new TextDecoder().decode(pt));logowanie(P);}
 catch(x){st.style.color="#b91c1c";st.textContent="Nieprawidłowe hasło.";}});

const norm=t=>String(t).normalize("NFD").replace(/[\\u0300-\\u036f]/g,"").replace(/ł/g,"l").replace(/Ł/g,"L").toLowerCase();
async function sha(t){const b=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(t));return[...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,"0")).join("")}
function otworz(P,L){const pre=L?"<script>window.WWW_LOGIN="+JSON.stringify(L).replace(/</g,"\\\\u003c")+";<\\/script>":"";
 const html=P.doc.replace("<head>","<head>"+pre);document.open();document.write(html);document.close()}
function logowanie(P){const O=P.login.osoby;let wyb=null;
 document.getElementById("f").outerHTML=`<form class="box" id="g" autocomplete="off"><h1>Logowanie</h1><p>Wpisz swoje nazwisko (można bez polskich znaków) i wybierz siebie z podpowiedzi, potem wpisz PIN otrzymany od administratora.</p>
 <input id="n" placeholder="Nazwisko" aria-label="Nazwisko" autofocus><div id="pod" role="listbox"></div><input id="p" type="text" placeholder="PIN" aria-label="PIN" autocapitalize="characters" autocomplete="off" autocorrect="off" spellcheck="false">
 <button id="z">Zaloguj</button><p id="st2"></p><p><a href="#" id="bez">Tylko materiały szkoleniowe, bez logowania</a></p></form>`;
 const n=document.getElementById("n"),pod=document.getElementById("pod"),st=document.getElementById("st2");
 n.addEventListener("input",()=>{wyb=null;const q=norm(n.value.trim());pod.innerHTML="";if(q.length<2)return;
  O.filter(o=>norm(o[1]).split(/[\\s-]+/).some(w=>w.startsWith(q))||norm(o[1]).startsWith(q)).slice(0,6).forEach(o=>{const b=document.createElement("button");b.type="button";b.className="pod";
   b.textContent=o[1]+(o[2]?" – "+o[2]:"");b.onclick=()=>{wyb=o;n.value=o[1];pod.innerHTML="";document.getElementById("p").focus()};pod.appendChild(b)})});
 document.getElementById("bez").onclick=e=>{e.preventDefault();otworz(P,null)};
 document.getElementById("g").addEventListener("submit",async e=>{e.preventDefault();st.style.color="#b91c1c";
  if(!wyb){const q=norm(n.value.trim());const m=O.filter(o=>norm(o[1])===q);if(m.length===1)wyb=m[0]}
  if(!wyb){st.textContent="Wybierz swoje nazwisko z podpowiedzi.";return}
  const pin=document.getElementById("p").value.trim().toUpperCase();const s=await sha("CURL-PIN|"+wyb[0]+"|"+pin);
  if(!pin||P.login.piny[wyb[0]]!==s){st.textContent="Nieprawidłowy PIN dla tej osoby. PIN nadaje administrator.";return}
  const L={kod:wyb[0],nazwa:wyb[1],sha:s};
  if(wyb[3]!=="PODGLAD"){otworz(P,Object.assign(L,{tryb:"pracownik"}));return}
  document.getElementById("g").innerHTML=`<h1>${wyb[1].replace(/[<&]/g,"")}</h1><p>Wybierz, co chcesz zrobić.</p><button id="t1">Podgląd całości (wszyscy pracownicy, wyniki, dokumenty – bez zmian)</button>${wyb[4]?'<button id="t2" style="background:#555">Mój test i moje dokumenty</button>':''}`;
  document.getElementById("t1").onclick=()=>otworz(P,Object.assign(L,{tryb:"podglad",rek:P.login.podglad.rek,odswiezono:P.login.podglad.odswiezono}));
  if(wyb[4])document.getElementById("t2").onclick=()=>otworz(P,Object.assign(L,{tryb:"pracownik"}))})}
})();</script></body></html>''' % (TYTUL, TYTUL, OPIS, b64(salt), b64(iv), ITER, b64(ct))
os.makedirs(f'{OUT}/{TRYB}', exist_ok=True)
open(f'{OUT}/{TRYB}/index.html', 'w', encoding='utf8').write(loader)
print(f'WERSJA {TRYB.upper()} (szyfrowana):', f'{OUT}/{TRYB}/index.html', len(loader.encode()) // 1024, 'KB; sha256 treści', hashlib.sha256(doc.encode()).hexdigest()[:12])

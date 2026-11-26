# Rama aplikacji CURL na stronach www – UKŁAD (makieta projektu wspolne/projekt/strona/makieta, zasady N-01..N-11, W-19, W-20,
# D-07..D-12 w projekt_strony.sqlite; TS 19.11.2026 20:49 „Układ, komputer, Alarm, szkolenie”, 21:23, 22:06–22:18).
# Wcześniej (dec. 193, TS 19.11.2026 09:20): pasek z zakładkami, przycisk ☰ i kafle – zastąpione jednym systemem nawigacji (W-20, N-07).
# Wstawia do treści strony (przed zaszyfrowaniem):
#  - pasek górny .pasek (tytuł ekranu, ← do ekranu nadrzędnego albo ✕ w module), bez okruszków (N-08);
#  - pasek dolny nav.dol (< 840 px) / panel boczny (≥ 840 px): Szkolenie, Wiedza BHP, [Zarządzanie – podgląd], Konto, Alarm (N-07);
#  - ekrany: Szkolenie (tematy programu tej osoby z postępem, D-11), Temat (moduły tematu), Programy, Wiedza BHP, Zarządzanie, Konto;
#  - arkusz Alarm (112, 998, 999; adres, miejsce zbiórki i numery wewnętrzne tylko z bazy – brak źródła = wiersz pominięty,
#    luka tylko w danych wewnętrznych data-brak; TS 20.11.2026 10:13: w wydaniu nie piszemy, że czegoś brakuje);
#  - moduł m* w krokach: jeden ekran = jeden krok, adres #m5/2/3 (replaceState), wznowienie, Wstecz/Dalej/Alarm (N-04, N-06).
# Źródła (tylko odczyt): układ, tytuły modułów, grupy, etykiety tematów, paleta = projekt_strony.sqlite (jedyne źródło zasad wyglądu);
# programy szkoleń = bhp_rejestr.program_szkolenia; napisy = ustawienie (RAMA_*); opisy kafli Wiedzy = aplikacja_kafel_aktualny i
# MANIFEST.json części zarządzania BHP (kafel, kafel_opis, role). Niezgodność = STOP budowy strony. Bez LLM, bez wymyślania treści:
# kroki modułu powstają z istniejących akapitów, list, rysunków i tabel (podział po nagłówkach części i liczbie słów, D-10).
# Funkcja wstaw(doc, tryb) zwraca nową treść; tryb = 'pelny' | 'pracownik'.
import json, re, os, sys, base64, hashlib, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ust_szkolen import polacz
ROLE = {'PRACOWNIK', 'PODGLAD'}
PROJEKT_STRONY = '/mnt/project-files/wspolne/projekt/strona/projekt_strony.sqlite'
MANIFEST_SYSTEMU = '/mnt/project-files/bhp/system/do_aplikacji/MANIFEST.json'
# programy na ekranie Szkolenie (D-11): wymóg → sekcja kursu, z której etykiety bierze się nazwa programu
PROGRAMY = (('INSTR_OGOLNY', 'szkwstepne', ''), ('OKR_CURL_2026_11', 'szkokresowe', ''), ('OKR_KIER', 'szkokresowe', ' dla kierujących'))
# sekcje Wiedzy z części zarządzania BHP (fragment MANIFEST): wiersz układu → fragment; „pomieszczenia” po „mapa”
WIEDZA_FRAGMENT = {'mapa': 'mapa', 'strefy': 'srodki'}
# powrót ← z dokumentu do ekranu części (N-08); przewijanie dokumentu tylko z listy wyjątków (N-02, przewijanie_wyjatek)
RODZIC = {'SZKOLENIE': '#programy', 'WIEDZA': '#wiedza', 'ZARZADZANIE': '#bhp/ludzie', 'SPRAWY': '#sprawy', 'KONTO': '#konto'}
# Etap 2 (TS 26.11.2026 19:30 UTC, W-319/Z-380, propozycja – bez wydania): BHP w jednym oknie. Jedno menu ramy:
# Szkolenie, Wiedza BHP, BHP (Mapa obiektu, Środki ochrony, Pracownicy i dokumenty), Moje sprawy, Konto, Alarm.
# Strony części zarządzania BHP (/pelny/aplikacja/*.html) są pokazywane wewnątrz ramy (ekran #bhp/<strona>), bez ich paska.
BHP_STRONY = (('mapa', 'mapa.html'), ('srodki', 'srodki.html'), ('ludzie', 'ludzie.html'))
BHP_LUDZIE_STRONY = ('szkolenia.html', 'dokumenty.html')   # dalsze strony „Pracownicy i dokumenty”
BHP_DUBLE_WIEDZY = ('mapa', 'pomieszczenia', 'srodki')     # fragmenty obiektu w Wiedzy, które dla podglądu są już w BHP
PRZEWIJANIE = {'ZARZADZANIE': 'tabela'}
EKRANY = ('szkolenie', 'temat', 'programy', 'wiedza', 'bhp', 'sprawy', 'konto')


def _projekt():
    c = sqlite3.connect(f'file:{PROJEKT_STRONY}?mode=ro', uri=True)
    c.row_factory = sqlite3.Row
    return c


def dane():
    db = polacz()
    U = dict(db.execute("select klucz, wartosc from ustawienie_aktualne where czesc='SZKOLENIA' and klucz like 'RAMA_%'"))
    for k in ('RAMA_NAZWA', 'RAMA_PODPIS', 'RAMA_WYLOGUJ', 'RAMA_ZMIEN_OSOBE', 'RAMA_LOGO', 'RAMA_DZIENNIK_WEJSC'):
        assert U.get(k), f'STOP rama: brak ustawienia {k} w tabeli ustawienie'
    assert U['RAMA_DZIENNIK_WEJSC'] in ('0', '1'), 'STOP rama: RAMA_DZIENNIK_WEJSC to 0 albo 1'
    kafle = db.execute('select kod, nazwa, opis, sekcja, role from aplikacja_kafel_aktualny order by kolejnosc, kod').fetchall()
    for kod, _, _, _, role in kafle:
        assert set(role.split(',')) <= ROLE, f'STOP rama: kafel {kod} ma nieznaną rolę {role}'
    if U['RAMA_LOGO'] != 'BRAK':
        assert re.fullmatch(r'[0-9a-f]{64}', U['RAMA_LOGO']), 'STOP rama: RAMA_LOGO to BRAK albo sha256 obrazu'
        assert db.execute("select count(*) from obraz_odbior where ident='LOGO_APLIKACJI' and sha256_pliku=? and werdykt='DOPUSZCZONY'",
                          (U['RAMA_LOGO'],)).fetchone()[0], 'STOP D-134: logo nie jest dopuszczone w rejestrze obrazów (obraz_odbior)'
        logo_svg()  # plik o tym skrócie musi istnieć
    prog = db.execute('select wymog_id, temat_nr, temat, moduly_kursu from program_szkolenia order by wymog_id, temat_nr').fetchall()
    obiekt = json.loads(dict(db.execute("select klucz, wartosc from ustawienie_aktualne where klucz='OBIEKT_ZAKLADKI'")).get('OBIEKT_ZAKLADKI', '[]'))
    return U, kafle, prog, obiekt


def logo_svg(sha=None):
    """Logo aplikacji (RAMA_LOGO): plik bhp/obrazy_aplikacji/<sha256>.svg.b64; skrót pliku = klucz; bez kodu i odnośników zewnętrznych."""
    if sha is None:
        sha = dict(polacz().execute("select klucz, wartosc from ustawienie_aktualne where czesc='SZKOLENIA' and klucz='RAMA_LOGO'")).get('RAMA_LOGO', 'BRAK')
    if sha == 'BRAK':
        return None
    # base64 (.svg.b64): dysk wspólny dopisuje do zapisywanych SVG metadane pochodzenia (C2PA), co zmieniłoby skrót
    raw = base64.b64decode(open(f'/mnt/project-files/bhp/obrazy_aplikacji/{sha}.svg.b64', 'rb').read())
    assert hashlib.sha256(raw).hexdigest() == sha, 'STOP D-134: plik logo różni się od skrótu RAMA_LOGO'
    assert not re.search(rb'<script|<foreignObject|<image|\bon\w+=|(?:xlink:)?href="(?!#)', raw, re.I), 'STOP logo: SVG z kodem albo odnośnikiem'
    return raw


def logo_img(wys, sha=None):
    """<img> z logo (data:image/svg+xml) na jasnym tle (TS 19.11: na ciemnej zieleni za słaby kontrast); pusty napis, gdy logo BRAK."""
    raw = logo_svg(sha)
    if raw is None:
        return ''
    return (f'<span class="logo_curl" style="display:inline-flex;align-items:center;justify-content:center;background:#fff;border-radius:50%;'
            f'width:{wys + 8}px;height:{wys + 8}px;flex:none;box-shadow:0 0 0 1px rgba(0,0,0,.08)"><img src="data:image/svg+xml;base64,'
            f'{base64.b64encode(raw).decode()}" alt="" width="{wys}" height="{wys}" style="width:{wys}px;height:{wys}px"></span>')


def _e(t):
    return str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


# Napisy ekranów wyłącznie z napis_wzorcowy (projekt_strony.sqlite, W-21, TS 19.11 23:32–23:33); brak klucza = STOP
NAPISY = ('TEST_ZABLOK', 'TEST_OTWARTY', 'STAN_BIEZACY', 'STAN_UKONCZONY', 'ZMIEN_PROGRAM', 'DALEJ_MODUL', 'ZAKRES_TEMATU',
          'PROGRAM_WYBRANY', 'DOKUMENT_KONIEC', 'TEST_UWAGA', 'ALARM_ZADZWON', 'ALARM_112', 'ALARM_ZGLOSZENIE', 'ALARM_ADRES',
          'ALARM_ZBIORKA', 'ALARM_PIERWSZA_POMOC', 'KONTO_ZALOGOWANO')


def napisy(pj):
    t = dict(pj.execute('select klucz, tekst from napis_wzorcowy'))
    brak = [k for k in NAPISY if not (t.get(k) or '').strip()]
    assert not brak, f'STOP rama: brak napisu wzorcowego {brak} w napis_wzorcowy (projekt_strony.sqlite)'
    N = {}
    for k in NAPISY:
        v = re.sub(r' \([^()]*\)$', '', t[k].strip())   # opis położenia w nawiasie na końcu nie jest napisem
        if k == 'ALARM_ZADZWON':
            v = v.split(' – ', 1)[0]                     # „📞 Zadzwoń – przycisk po prawej…”: napis przed opisem
        N[k] = v.strip()
    assert ': ' in N['ALARM_ZGLOSZENIE'], 'STOP rama: napis ALARM_ZGLOSZENIE bez etykiety „…: ”'
    # adres, zbiórka, pierwsza pomoc: sama etykieta (projekt_strony, dopisek 038, 21.11.2026); wartość tylko z bazy kadr
    for k in ('ALARM_ADRES', 'ALARM_ZBIORKA', 'ALARM_PIERWSZA_POMOC'):
        assert N[k].split(': ', 1)[0].strip(), f'STOP rama: napis {k} bez etykiety'
        assert 'uzupełni' not in N[k], f'STOP rama: napis {k} zapowiada brak (TS 20.11.2026 10:13)'
    return N


def _moduly(spis, znane):
    """'m2–m5, ŚOI' → ['m2','m3','m4','m5','soi'] (zakres po numerze; ŚOI = sekcja soi). Nieznany element = STOP."""
    out = []
    for t in [x.strip() for x in spis.split(',') if x.strip()]:
        m = re.fullmatch(r'm(\d+)\s*[–-]\s*m(\d+)', t)
        if m:
            out += [f'm{i}' for i in range(int(m.group(1)), int(m.group(2)) + 1)]
        elif t == 'ŚOI':
            out.append('soi')
        else:
            assert re.fullmatch(r'm\d+', t), f'STOP rama: nieznany moduł „{t}” w program_szkolenia.moduly_kursu'
            out.append(t)
    for m in out:
        assert m in znane, f'STOP rama: moduł {m} z programu bez tytułu w modul_tytul (projekt_strony.sqlite)'
    return out


# Kolory wyłącznie z paleta_token (projekt_strony.sqlite); w CSS jako zmienne --r-<token>
CSS = '''<style id="rama_styl">/*RAMA-APLIKACJI*/
/* jeden jasny motyw (TS 19.11.2026 19:07–19:13): ustawienie ciemne telefonu nie zmienia kolorów */
:root{color-scheme:light;__ZMIENNE__}
html body{font-size:18px;background:var(--r-bg);color:var(--r-ink)}/* tekst główny 18 px (W-01) */
/* jeden system nawigacji (W-20, N-07): bez nagłówka kursu, spisu ☰, przycisków poprzedni/następny i spisu części modułu */
header.top,#navtoggle,nav#nav,nav.mods,.navrow,#dogory,.mtoc,#podglad_baner,#kurs_wersja_stopka{display:none!important}
.layout{display:block!important}
/* adres #sekcja nie przewija strony do sekcji pod paskiem: ekran zawsze od góry */
main section{scroll-margin-top:300vh}
.wrap{max-width:960px!important;margin:0 auto!important;padding:12px max(16px,env(safe-area-inset-left,0px)) 76px!important;box-sizing:border-box}
/* nic nie rozszerza strony poza ekran telefonu (TS 19.11.2026 19:17): szerokie tabele i listy wyboru w swoim polu */
.tablewrap,.tbl,.szk,.rmx{overflow-x:auto;max-width:100%}
@media (max-width:700px){main :not(.tablewrap):not(.tbl):not(.szk)>table{display:block;overflow-x:auto;max-width:100%;min-width:0!important}main select{max-width:100%}main label{max-width:100%;overflow-wrap:anywhere}}
/* pasek górny (K-PASEK-*): pełna szerokość, 56 px, przyklejony */
.pasek{position:sticky;top:0;z-index:50;height:56px;display:flex;align-items:center;gap:12px;padding:0 12px;margin:0;width:100%;box-sizing:border-box;background:var(--r-primary);color:var(--r-surface)}
.pasek .tytul{font-weight:600;font-size:18px;flex:1;min-width:0;white-space:nowrap;overflow:hidden}
.pasek .ikona{width:48px;height:48px;flex:none;display:grid;place-items:center;color:var(--r-surface);font-size:22px;text-decoration:none;margin-left:-8px}
.pasek .ikona[hidden],.pasek .logo_curl[hidden]{display:none!important}
/* pasek dolny (K-DOL-*), na komputerze panel boczny 240 px z Alarmem na górze (K-BOK-*) */
nav.dol{position:fixed;left:0;right:0;bottom:0;z-index:60;display:grid;grid-template-columns:repeat(var(--n,4),minmax(0,1fr));background:var(--r-surface);border-top:1px solid var(--r-line);padding-bottom:env(safe-area-inset-bottom);height:68px;box-sizing:border-box;margin:0}
nav.dol a{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;text-decoration:none;color:var(--r-muted);font-size:13px;font-weight:600;min-height:56px;min-width:0;text-align:center}
nav.dol a .i{font-size:22px;line-height:1.2}nav.dol a.akt{color:var(--r-primary)}nav.dol a.akt .i{background:var(--r-primary_bg);border-radius:99px;padding:0 14px}
nav.dol a.alarm{color:var(--r-surface);background:var(--r-fire);margin:6px;border-radius:12px}
nav.dol a .kr{display:block}nav.dol a .dl,nav.dol a.pod{display:none}
.bhp-ramka{display:block;width:100%;border:0;min-height:60vh;background:var(--r-surface)}
a:focus-visible,button:focus-visible{outline:3px solid var(--r-mand);outline-offset:2px}
.pasek a:focus-visible,nav.dol a.alarm:focus-visible{outline:3px solid var(--r-surface);box-shadow:0 0 0 5px var(--r-ink)}
@media(min-width:840px){
 nav.dol{top:56px;bottom:0;right:auto;width:240px;height:auto;display:flex;flex-direction:column;justify-content:flex-start;padding:8px 0;border-top-width:0;border-right:1px solid var(--r-line)}
 nav.dol a{flex-direction:row;justify-content:flex-start;gap:12px;padding:0 16px;min-height:52px;font-size:16px;text-align:left}
 nav.dol a.alarm{order:-1;margin:4px 12px 12px;justify-content:center}
 nav.dol a .dl{display:block}nav.dol a .kr{display:none}
 nav.dol a.pod{display:flex;min-height:40px;padding-left:52px;font-size:15px;font-weight:500}nav.dol a.pod.akt{background:var(--r-primary_bg)}
 .wrap{margin:0 0 0 264px!important;padding-bottom:24px!important}
}
/* przy bardzo niskim oknie i powiększeniu paski nie zasłaniają treści (N-03) */
@media (max-height:479px){.pasek{position:static}nav.dol{position:static;height:auto}.wrap{padding-bottom:12px!important}}
/* ekrany ramy (makieta: lista, wiersz, karta postępu, kafle, konto) */
.ekran_ramy .tresc{max-width:960px}
@media(max-width:559px){.kafle.zwin{display:none}}@media(min-width:560px){.wiedza-krotka{display:none}}
.ekran_ramy h2{font-family:Archivo,"Arial Narrow",Arial,sans-serif}
.karta-postepu{background:var(--r-surface);border:1px solid var(--r-line);border-radius:12px;padding:14px 16px;margin:0 0 12px;box-shadow:0 1px 2px rgb(22 33 27/.08)}
.karta-postepu h2{font-size:20px;margin:0 0 2px;color:var(--r-ink)}
.naglowek-spraw{display:flex;align-items:baseline;justify-content:space-between;gap:12px}
.naglowek-spraw .wszystkie{font-size:16px;font-weight:600;color:var(--r-primary);text-decoration:none;white-space:nowrap;font-family:inherit}
.postep{height:10px;background:var(--r-track);border-radius:99px;overflow:hidden;margin:8px 0 4px}.postep i{display:block;height:100%;background:var(--r-primary)}
.ekran_ramy .meta,.arkusz .meta{font-size:15px;color:var(--r-muted);margin:0}
.ekran_ramy .btn,.rama_koniec .btn{display:flex;align-items:center;justify-content:center;min-height:52px;border-radius:8px;font-weight:600;font-size:17px;text-decoration:none;padding:0 16px;text-align:center;box-sizing:border-box}
.btn.glowny{background:var(--r-primary);color:var(--r-surface);margin-top:10px;width:100%;border:0}.btn.glowny.alarmowy{background:var(--r-fire)}
a,button{outline-offset:2px}
/* W-10 (projekt_strony K-PRZYCISK-CEL): każdy przycisk .btn, także w treści szkoleń, ma cel dotykowy co najmniej 52 px */
main .btn{min-height:52px;box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center}
/* W-17 (K-TAG-INFO-TEKST): znaczniki DOBRZE/ŹLE przy rysunkach to opis, nie stan – napis w kolorze tekstu na jasnym tle;
   kolory stanu tylko dla .tag.pilne (po terminie) i .tag.termin (zbliża się termin) */
main .tag{color:var(--r-ink)}main .tag.ok{background:var(--r-primary_bg);color:var(--r-ink);border:2px solid var(--r-primary)}
main .tag.bad{background:var(--r-surface);color:var(--r-ink);border:2px solid var(--r-fire)}
main .tag.pilne{background:var(--r-fire);color:var(--r-surface)}main .tag.termin{background:var(--r-warn_bg);color:var(--r-warn_ink);border:1px solid var(--r-warn)}
/* klasy z makiety: odpowiedź w pytaniu (.odp, K-ODP-*) i informacja zwrotna po odpowiedzi (.wynik, K-WYNIK-TLO) */
main .odp{min-height:48px;box-sizing:border-box;border-color:var(--r-border)}
main .wynik{background:var(--r-surface)}
.lista{background:var(--r-surface);border:1px solid var(--r-line);border-radius:12px;overflow:hidden;margin:0 0 14px}
.lista h2{font-size:14px;letter-spacing:.06em;text-transform:uppercase;color:var(--r-muted);font-family:inherit;font-weight:700;padding:8px 16px 4px;margin:0}
.wiersz{display:flex;align-items:center;gap:12px;min-height:52px;padding:6px 16px;border-top:1px solid var(--r-line);color:var(--r-ink);text-decoration:none;font-weight:600;box-sizing:border-box}
.lista h2+.wiersz,.lista .wiersz:first-child{border-top:0}
/* W-19 (22.11.2026): ostatnia lista ekranu bez dolnego marginesu, pas pod treścią = pasek dolny 68 px + 8 px – ekran Szkolenie mieści się w 664 px */
.ekran_ramy .tresc>.lista:last-child{margin-bottom:0}
.wiersz span{flex:1;min-width:0}.wiersz small{display:block;font-size:15px;font-weight:400;color:var(--r-muted)}
.wiersz .st{flex:none;font-size:15px;font-weight:700;color:var(--r-muted)}
.wiersz[aria-current]{background:var(--r-primary_bg)}.wiersz[aria-current] .st{color:var(--r-primary)}
.ekran_ramy p.zakres{font-size:14px;line-height:1.35}
.polozenie{font-size:15px;color:var(--r-muted);margin:0 0 4px}
.krok-wsk{font-size:15px;font-weight:700;color:var(--r-ink);margin:0 0 6px}
.ekran_ramy h2.krok{font-size:22px;line-height:1.25;margin:4px 0 10px;color:var(--r-ink)}
.kafle{display:grid;grid-template-columns:minmax(0,1fr);gap:12px}
@media(min-width:560px){.kafle{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}}
.kafel{display:flex;gap:14px;align-items:center;min-height:76px;background:var(--r-surface);border:1px solid var(--r-line);border-left:4px solid var(--r-primary);border-radius:12px;padding:12px 14px;text-decoration:none;color:var(--r-ink);box-shadow:0 1px 2px rgb(22 33 27/.08);box-sizing:border-box}
.kafel .ik{flex:none;width:44px;height:44px;border-radius:50%;display:grid;place-items:center;font-size:22px;font-style:normal;background:var(--r-primary_bg)}
.kafel b{display:block;color:var(--r-ink);font-size:18px;font-weight:600;line-height:1.3}
.kafel span{display:block;font-size:15px;color:var(--r-muted);line-height:1.35}
.menu-konta{background:var(--r-surface);border:1px solid var(--r-line);border-radius:12px;overflow:hidden}
.menu-konta a{display:flex;align-items:center;gap:12px;min-height:56px;padding:0 16px;border-top:1px solid var(--r-line);text-decoration:none;color:var(--r-ink);font-weight:600}
.menu-konta a:first-child{border-top:0}.menu-konta a.wyl{color:var(--r-ink)}.menu-konta a[hidden]{display:none}
.powitanie{font-size:15px;color:var(--r-muted);margin:0 0 8px}
.uwaga-pasek{display:flex;align-items:center;gap:10px;flex-wrap:wrap;background:var(--r-warn_bg);border:1px solid var(--r-warn);border-left:6px solid var(--r-warn);border-radius:12px;padding:12px 14px;margin:0 0 16px;color:var(--r-ink);font-weight:600}
.uwaga-pasek a{color:var(--r-ink)}
.rama_koniec{margin:20px 0 8px}
/* arkusz Alarm: pierwsze dotknięcie otwiera panel, numer dzwoni drugim (W-11) */
.arkusz{position:fixed;inset:0;z-index:90;background:rgb(0 0 0/.4);display:flex;align-items:flex-end}.arkusz[hidden]{display:none}
.arkusz .panel{width:100%;max-height:100%;overflow-y:auto;box-sizing:border-box;background:var(--r-surface);color:var(--r-ink);border-radius:16px 16px 0 0;padding:16px 16px calc(16px + env(safe-area-inset-bottom))}
.arkusz h2{font-size:22px;color:var(--r-fire);margin:0 0 4px;font-family:Archivo,Arial,sans-serif}
.tel{display:flex;align-items:center;gap:14px;min-height:60px;border:2px solid var(--r-fire);border-radius:12px;padding:6px 14px;margin:6px 0;text-decoration:none;color:var(--r-ink);box-sizing:border-box}
.tel b{font-size:26px;color:var(--r-fire);min-width:64px;font-family:Archivo,Arial,sans-serif}
.tel.t112{min-height:72px}.tel.t112 b{font-size:32px}
.tel.wewn{border-color:var(--r-primary);flex-wrap:wrap;row-gap:4px}.tel.wewn b{font-size:18px;color:var(--r-primary);min-width:auto;flex-basis:100%}.tel.wewn span small{white-space:nowrap}
.tel span{flex:1;min-width:0}.tel span small{display:block;font-size:14px;color:var(--r-muted)}.tel .zadzwon{font-style:normal;font-weight:700;white-space:nowrap;background:var(--r-fire);color:var(--r-surface);border-radius:10px;padding:10px 12px;font-size:15px}
.adres p{margin:4px 0}
.adres{background:var(--r-bg);border:1px solid var(--r-line);border-radius:12px;padding:8px 14px;margin:6px 0;font-size:16px}
.zamknij{display:block;width:100%;min-height:52px;margin-top:8px;border:2px solid var(--r-border);background:var(--r-surface);color:var(--r-ink);border-radius:8px;font:inherit;font-weight:600;cursor:pointer}
@media(min-width:840px){.arkusz{align-items:center;justify-content:center}.arkusz .panel{max-width:480px;border-radius:16px}}
/* moduł w krokach (N-04, N-06): widać tylko bloki bieżącego kroku; nagłówek modułu i części jest w pasku i we wskaźniku */
main section.krokowy>.mhead,.rk-h3{display:none!important}
main section.krokowy .rk-blok:not(.rk-on){display:none!important}
main section.krokowy figure img{max-height:42vh;width:auto!important;max-width:100%;object-fit:contain;display:block;margin:0 auto}
@media(min-width:840px){.lista.dwie{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.lista.dwie .wiersz:nth-child(2){border-top:0}.lista.dwie .wiersz:nth-child(odd){border-right:1px solid var(--r-line)}}
.rk-glowa{margin:0 0 10px}
@media print{.pasek,nav.dol,.arkusz,.rk-glowa,.rama_koniec{display:none!important}main section.krokowy .rk-blok{display:block!important}.wrap{margin:0!important;padding:0!important}}
</style>'''

JS = r'''<script>/*RAMA-APLIKACJI-JS*/(function(){const R=window.RAMA_APLIKACJI;
const L=window.WWW_LOGIN||null;const rola=L&&L.tryb==="podglad"?"PODGLAD":"PRACOWNIK";
const P=(function(){try{return window.parent!==window&&window.parent.WWW_RAMA?window.parent.WWW_RAMA:null}catch(e){return null}})();
const $=i=>document.getElementById(i);const H=t=>String(t==null?"":t).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const LS={get(k,d){try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
const SS={get(k){try{return JSON.parse(sessionStorage.getItem(k)||"null")}catch(e){return null}},set(k,v){try{sessionStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
const jest=i=>{const e=document.getElementById(i);return !!e&&e.tagName==="SECTION"&&!!e.closest("main")};
/* dziennik wejść (RAMA_DZIENNIK_WEJSC): typ „wejscie”, kod osoby, skrót PIN-u */
let ZU=null;function wpis(z){if(!(R.dziennik&&L&&L.kod&&L.sha&&ZU))return false;try{return navigator.sendBeacon(ZU,JSON.stringify({typ:"wejscie",kod_osoby:L.kod,pin_skrot:L.sha,zdarzenie:z,tryb:L.tryb||"",strona:location.pathname}))}catch(e){return false}}
if(R.dziennik&&L&&L.kod)fetch("zapis.json",{cache:"no-store"}).then(r=>r.json()).then(j=>{if(j&&/^https:\/\/script\.google\.com\/macros\/s\/[\w-]+\/exec$/.test(j.url||"")){ZU=j.url;wpis("ZALOGOWANIE")}}).catch(()=>{});
/* karty charakterystyki tylko po zalogowaniu (ZG-1119-1531-1): odnośnik sds/<nazwa>.pdf otwiera odszyfrowany plik */
document.addEventListener("click",e=>{const a=e.target.closest&&e.target.closest("a[href]");if(!a)return;const m=(a.getAttribute("href")||"").match(/^(?:\.\.\/)?sds\/([A-Za-z0-9_.-]+\.pdf)$/);
 if(!m||!P||!P.sds)return;e.preventDefault();let w=null;try{w=window.open("","_blank")}catch(x){}
 P.sds(m[1],w).catch(()=>{if(w)try{w.close()}catch(x){}alert("Nie udało się otworzyć karty charakterystyki.")})},true);
/* postęp: ukończone moduły (ten sam zapis co w kursie: bhp_done) */
const ukonczone=()=>new Set(LS.get("bhp_done",[]));
function ukoncz(id){const s=ukonczone();s.add(id);LS.set("bhp_done",[...s]);try{if(typeof done!=="undefined"&&done&&done.add)done.add(id)}catch(e){}}
function program(){const w=LS.get("rama_program",null);if(w&&R.prog[w])return w;
 const p=L&&window.SZK&&SZK.PROF?SZK.PROF[L.kod]:null;return p?(p.kier?R.domyslny.kier:R.domyslny.prac):R.domyslny.brak}
const modulyProg=pk=>{const o=[];R.prog[pk].tem.forEach(t=>t.m.forEach(m=>{if(jest(m)&&!o.includes(m))o.push(m)}));return o};
const tyt=id=>R.tyt[id]||((document.getElementById(id)||{}).dataset||{}).title||id;
const skad=id=>{const s=SS.get("rama_skad");return s&&s.id===id?s.wroc:null};
const rodzic=id=>skad(id)||R.rodzic[id]||"#szkolenie";
/* zapamiętanie, skąd otwarto ekran (← i ✕ wracają tam, nie do historii przeglądarki; N-08) */
document.addEventListener("click",e=>{const a=e.target.closest&&e.target.closest(".ekran_ramy a[href^='#'],.rama_koniec a[href^='#']");if(!a)return;
 const id=a.getAttribute("href").slice(1).split("/")[0];if(id&&!R.ekrany.includes(id))SS.set("rama_skad",{id,wroc:location.hash||"#"+start()})});
const start=()=>rola==="PODGLAD"&&R.bhp.length?"sprawy":"szkolenie";
/* ── ekrany ── */
const N=R.napis,F=(s,o)=>s.replace(/\{([^}]+)\}/g,(x,k)=>k in o?o[k]:x);
function ekranSzkolenie(){const pk=program(),pr=R.prog[pk],d=ukonczone(),ms=modulyProg(pk);const n=ms.filter(m=>d.has(m)).length;
 const nast=ms.find(m=>!d.has(m));let biez=-1;
 const w=pr.tem.map((t,i)=>{const mm=t.m.filter(jest),gotowy=mm.length&&mm.every(m=>d.has(m));if(!gotowy&&biez<0)biez=i;
  return `<a class="wiersz" href="#temat/${pk}/${t.nr}"${biez===i?' aria-current="true"':""}><span>${t.nr}. ${H(t.t)}</span><b class="st">${gotowy?H(N.STAN_UKONCZONY):biez===i?H(N.STAN_BIEZACY):""}</b></a>`}).join("");
 const tg=pr.tem.filter(t=>{const mm=t.m.filter(jest);return mm.length&&mm.every(m=>d.has(m))}).length;
 const test=jest("test")?`<a class="wiersz" href="#test"><span>Test końcowy</span><b class="st">${nast?H(N.TEST_ZABLOK):H(N.TEST_OTWARTY)}</b></a>`:"";
 $("szkolenie").innerHTML=`<div class="tresc"><div class="karta-postepu"><h2 class="naglowek-spraw"><span>${H(pr.t)}</span><a class="wszystkie" href="#programy">${H(N.ZMIEN_PROGRAM)}</a></h2>
  <p class="meta">Ukończone tematy: ${tg} z ${pr.tem.length}</p>
  <div class="postep" role="progressbar" aria-label="Ukończone tematy" aria-valuemin="0" aria-valuemax="${pr.tem.length}" aria-valuenow="${tg}"><i style="width:${Math.round(100*tg/pr.tem.length)}%"></i></div>
  ${nast?`<a class="btn glowny" href="#${nast}">${H(F(N.DALEJ_MODUL,{"tytuł":tyt(nast)}))}</a>`:jest("test")?`<a class="btn glowny" href="#test">Przejdź do testu</a>`:""}</div>
  <div class="lista${pr.tem.length>7?" dwie":""}">${w}${test}</div></div>`;
 return pr.t}
function ekranTemat(cz){const pk=R.prog[cz[1]]?cz[1]:program(),pr=R.prog[pk],t=pr.tem.find(x=>String(x.nr)===cz[2])||pr.tem[0],d=ukonczone();let biez=-1;
 const w=t.m.filter(jest).map((m,i)=>{const g=d.has(m);if(!g&&biez<0)biez=i;
  return `<a class="wiersz" href="#${m}"${biez===i?' aria-current="step"':""}><span>${H(tyt(m))}</span><b class="st">${g?H(N.STAN_UKONCZONY):biez===i?H(N.STAN_BIEZACY):""}</b></a>`}).join("");
 $("temat").innerHTML=`<div class="tresc"><p class="polozenie">${H(pr.t)} · temat ${t.nr} z ${pr.tem.length}</p><h2 class="krok">${H(t.t)}</h2>
  <div class="lista">${w}</div><p class="meta zakres">${H(F(N.ZAKRES_TEMATU,{"pełne brzmienie":t.pelny}))}</p></div>`;
 SS.set("rama_temat",{pk,nr:t.nr});return `Temat ${t.nr} z ${pr.tem.length}`}
function ekranProgramy(){const pk=program();
 const w=Object.keys(R.prog).map(k=>`<a class="wiersz" href="#szkolenie" data-program="${k}"${k===pk?' aria-current="true"':""}><span>${H(R.prog[k].t)}<small>${R.prog[k].tem.length} tematów</small></span><b class="st">${k===pk?H(N.PROGRAM_WYBRANY):""}</b></a>`).join("");
 const o=R.opisy.filter(x=>jest(x.id)).map(x=>`<a class="wiersz" href="#${x.id}"><span>${H(x.t)}</span></a>`).join("");
 $("programy").innerHTML=`<div class="tresc"><div class="lista"><h2>Programy szkoleń</h2>${w}</div>${o?`<div class="lista"><h2>Opis szkoleń</h2>${o}</div>`:""}</div>`;
 return "Szkolenia"}
function ekranWiedza(){const W=R.wiedza.filter(x=>jest(x.id)&&x.role.includes(rola)&&!(rola==="PODGLAD"&&R.bhp.length&&x.bhp));const k=W.map(x=>`<a class="kafel" href="#${x.id}"><i class="ik" aria-hidden="true">${x.ik}</i><div><b>${H(x.t)}</b>${x.o?`<span>${H(x.o)}</span>`:""}</div></a>`).join("");
 /* więcej niż 4 pozycje: na telefonie lista zamiast kafli, żeby ekran się nie przewijał (N-01) */
 const l=W.length>4?`<div class="lista wiedza-krotka">${W.map(x=>`<a class="wiersz" href="#${x.id}"><span>${H(x.t)}</span></a>`).join("")}</div>`:"";
 $("wiedza").innerHTML=`<div class="tresc"><div class="kafle${l?" zwin":""}">${k}</div>${l}</div>`;return R.czesci.WIEDZA}
/* ── BHP w jednym oknie (etap 2): lista części, „Pracownicy i dokumenty”, strona części zarządzania BHP w ramie ── */
const wiersz=(h,t,o)=>`<a class="wiersz" href="${H(h)}"><span>${H(t)}${o?`<small>${H(o)}</small>`:""}</span></a>`;
function ekranBhp(cz){const s=cz[1]||"";
 if(!s){$("bhp").innerHTML=`<div class="tresc"><div class="lista">${R.bhp.map(x=>wiersz("#bhp/"+x.id,x.t,x.o)).join("")}</div></div>`;return [R.czesci.BHP,null]}
 if(s==="ludzie"&&!cz[2]){const z=R.zarz.filter(x=>jest(x.id));
  $("bhp").innerHTML=`<div class="tresc"><div class="lista">${[{h:"#bhp/ludzie/strona",t:R.bhp.find(x=>x.id==="ludzie").strona_t}].concat(R.bhp_ludzie.map(x=>({h:"#bhp/"+x.plik.replace(/\.html$/,""),t:x.t}))).map(x=>wiersz(x.h,x.t)).join("")}</div>
   <div class="lista dwie">${z.map(x=>wiersz("#"+x.id,x.t)).join("")}</div></div>`;
  return [R.bhp.find(x=>x.id==="ludzie").t,"#bhp"]}
 const b=R.bhp.find(x=>x.id===s),l=R.bhp_ludzie.find(x=>x.plik===s+".html"),pl=s==="index"?"index.html":b?b.plik:l?l.plik:null;
 if(!pl){location.replace("#bhp");return ["",null]}
 bhpStrona(pl,cz.slice(s==="ludzie"?3:2).join("/"));
 if(s==="index")return [(R.sprawy.find(x=>x.h&&x.h.startsWith("#bhp/index"))||{}).t||R.czesci.SPRAWY,"#sprawy"];
 return [s==="ludzie"?b.strona_t:b?b.t:l.t,s==="ludzie"||!b?"#bhp/ludzie":"#bhp"]}
/* strona części zarządzania BHP w ramce: treść odszyfrowuje powłoka (P.strona), pasek tej części jest ukryty (tryb „w ramie”) */
let BHP_W=null;
function bhpStrona(pl,kot){const sec=$("bhp");$("main").setAttribute("data-przewijanie","dokument");
 if(BHP_W===pl+"#"+kot&&sec.querySelector("iframe"))return;BHP_W=pl+"#"+kot;
 if(!P||!P.strona){sec.innerHTML=`<div class="tresc"><div class="lista">${wiersz("aplikacja/"+pl,R.napis.BHP_OTWORZ||"Otwórz")}</div></div>`;return}
 sec.innerHTML=`<p class="meta" role="status">Otwieranie…</p>`;
 P.strona(pl).then(h=>{const f=document.createElement("iframe");f.className="bhp-ramka";f.title=pl;
  const css=`<style>/*w-ramie*/body>div[style*="sticky"]:first-child,nav.pasek{display:none!important}body{margin:0!important}</style>`;
  f.srcdoc=h.replace(/<\/head>/i,css+"</head>");sec.innerHTML="";sec.appendChild(f);
  f.addEventListener("load",()=>{const d=f.contentDocument;if(!d)return;const dop=()=>{f.style.height=d.documentElement.scrollHeight+"px"};dop();
   try{new ResizeObserver(dop).observe(d.body)}catch(e){}
   if(kot){const c=d.getElementById(kot);if(c)setTimeout(()=>window.scrollTo(0,c.getBoundingClientRect().top+f.getBoundingClientRect().top+scrollY-64),0)}
   d.addEventListener("click",e=>{const a=e.target.closest&&e.target.closest("a[href]");if(!a)return;const h=a.getAttribute("href")||"";
    let m=h.match(/^([a-z_]+)\.html(?:#(.*))?$/);
    if(m){e.preventDefault();location.hash="#bhp/"+(m[1]==="ludzie"?"ludzie/strona":m[1])+(m[2]?"/"+m[2]:"");return}
    if(/^\.\.\/?$/.test(h)){e.preventDefault();location.hash="#szkolenie";return}
    if(/^#/.test(h)){e.preventDefault();const c=d.getElementById(h.slice(1));if(c)window.scrollTo(0,c.getBoundingClientRect().top+f.getBoundingClientRect().top+scrollY-64)}},true)})
 }).catch(()=>{sec.innerHTML=`<div class="tresc"><p class="meta">${H(R.napis.BHP_BLAD||"Nie udało się otworzyć strony.")}</p></div>`})}
function ekranSprawy(){const z=R.sprawy.filter(x=>!x.id||jest(x.id));
 $("sprawy").innerHTML=`<div class="tresc"><div class="lista">${z.map(x=>wiersz(x.h||"#"+x.id,x.t,x.o)).join("")}</div></div>`;return R.czesci.SPRAWY}
function ekranKonto(){const o=R.konto.filter(x=>!x.id||jest(x.id));
 $("konto").innerHTML=`<div class="tresc">${L?`<p class="powitanie">${H(F(N.KONTO_ZALOGOWANO,{"imię i nazwisko":L.nazwa}))}</p>`:""}<div class="menu-konta">${o.map(x=>x.id?`<a href="#${x.id}"><span aria-hidden="true">${x.ik}</span>${H(x.t)}</a>`:
  `<a href="#konto" id="${x.akcja}"${x.akcja==="rama_wyloguj"?' class="wyl"':""}${x.akcja==="rama_zmien"&&!(L&&P)?" hidden":""}><span aria-hidden="true">${x.ik}</span>${H(x.t)}</a>`).join("")}</div></div>`;
 return R.czesci.KONTO}
/* ── moduł w krokach (D-10, N-04, N-06) ── */
const KR={};const CIEZKI="figure,table,.tbl,.conseq,.box,details,.note,.plan,.card,.rmx,.rmxfig,form,.hbox,.szk";
function kroki(sec){if(KR[sec.id])return KR[sec.id];const bl=[],cz=[R.wstep];
 const zbierz=par=>{for(const e of [...par.children]){if(e.matches("script,style,link,.mhead,.navrow,.mtoc,.rk-glowa,.rama_koniec")||e.hidden)continue;
  if(e.classList.contains("prose")){zbierz(e);continue}
  if(e.tagName==="H3"){cz.push(e.textContent.trim());e.classList.add("rk-h3");continue}
  const sl=(e.textContent||"").trim().split(/\s+/).filter(Boolean).length;bl.push({e,c:cz.length-1,w:sl,ci:e.matches(CIEZKI)||!!e.querySelector("img,svg,table,input,select,button,iframe")})}};
 zbierz(sec);const K=[];let k=null;
 for(const b of bl){if(!k||k.c!==b.c||((b.ci||k.ci||k.w+b.w>R.slowa)&&!k.dwukropek)){k={c:b.c,bl:[],w:0,ci:b.ci};K.push(k)}k.bl.push(b.e);k.w+=b.w;k.ci=k.ci||b.ci;k.dwukropek=!b.ci&&/:\s*$/.test(b.e.textContent||"");b.e.classList.add("rk-blok")}
 const uz=[...new Set(K.map(x=>x.c))];const ile={};K.forEach(x=>{x.p=uz.indexOf(x.c);ile[x.p]=(ile[x.p]||0)+1;x.s=ile[x.p]});
 const g=document.createElement("div");g.className="rk-glowa";sec.insertBefore(g,sec.firstChild);sec.classList.add("krokowy");
 return KR[sec.id]={K,cz:uz.map(c=>cz[c]),g}}
let MK=null;
function pokazKrok(sec,k){const D=kroki(sec);if(!D.K.length)return;k=Math.max(0,Math.min(k,D.K.length-1));
 D.K.forEach((x,i)=>x.bl.forEach(e=>e.classList.toggle("rk-on",i===k)));const x=D.K[k],t=SS.get("rama_temat"),pr=t&&R.prog[t.pk];
 const tm=pr&&pr.tem.find(y=>y.nr===t.nr&&y.m.includes(sec.id));
 D.g.innerHTML=`<p class="polozenie">${tm?H(pr.t)+" · temat "+tm.nr+" z "+pr.tem.length:H(R.grupa[sec.id]||"")} · krok ${k+1} z ${D.K.length}</p>
  <p class="krok-wsk">Część ${x.p+1} z ${D.cz.length} · ${H(D.cz[x.p])}</p>
  <div class="postep" role="progressbar" aria-label="Postęp modułu" aria-valuemin="1" aria-valuemax="${D.K.length}" aria-valuenow="${k+1}"><i style="width:${Math.round(100*(k+1)/D.K.length)}%"></i></div>`;
 const z=LS.get("rama_krok",{});z[sec.id]=k;LS.set("rama_krok",z);MK={sec,k,n:D.K.length};
 const a="#"+sec.id+"/"+(x.p+1)+"/"+x.s;if(location.hash!==a){try{history.replaceState(history.state,"",a)}catch(e){}try{if(P)P.adres(a)}catch(e){}}
 window.scrollTo(0,0);nawigacja("modul")}
function wejdzModul(sec,cz){const D=kroki(sec);let k=-1;
 if(cz.length>=3)k=D.K.findIndex(x=>x.p===+cz[1]-1&&x.s===+cz[2]);if(k<0){const z=LS.get("rama_krok",{})[sec.id];k=Number.isInteger(z)&&z<D.K.length?z:0}
 pokazKrok(sec,k)}
function wyjdzModul(id){const t=SS.get("rama_temat");const w=skad(id)||(t?`#temat/${t.pk}/${t.nr}`:"#szkolenie");location.hash=w}
/* ── pasek górny i dolny ── */
function pasek(t,wstecz,ik){const a=$("rama_wstecz");$("rama_tytul").textContent=t;a.hidden=!wstecz;if(wstecz){a.href=wstecz;a.textContent=ik;a.setAttribute("aria-label",ik==="✕"?"Zamknij moduł":"W górę")}
 const l=document.querySelector("#rama .logo_curl");if(l)l.hidden=!!wstecz;document.title=t?t+" – "+R.nazwa:R.nazwa}
function nawigacja(tryb,akt,pod){const n=$("rama_dol");let h="";
 if(tryb==="modul"){const ost=MK&&MK.k===MK.n-1;h=`<a href="#" data-krok="-1"><span class="i" aria-hidden="true">←</span>Wstecz</a><a class="akt" href="#" data-krok="1"><span class="i" aria-hidden="true">${ost?"✓":"→"}</span>${ost?"Zakończ":"Dalej"}</a>`;n.style.setProperty("--n",3)}
 else{const cz=R.nawig.filter(c=>c.rola.includes(rola));n.style.setProperty("--n",cz.length+1);
  h=cz.map(c=>`<a href="#${c.id}"${c.cz===akt?' class="akt" aria-current="page"':""}><span class="i" aria-hidden="true">${c.ik}</span><span class="dl">${H(c.t)}</span><span class="kr">${H(c.krotko||c.t)}</span></a>`
   /* na komputerze (panel boczny) pozycje części BHP pod nią; na telefonie ukryte – lista na ekranie BHP */
   +(c.id==="bhp"?R.bhp.map(x=>`<a class="pod${pod===x.id?" akt":""}" href="#bhp/${x.id}"${pod===x.id?' aria-current="page"':""}>${H(x.t)}</a>`).join(""):"")).join("")}
 n.innerHTML=h+`<a class="alarm" href="#" id="rama_alarm_przycisk" role="button" aria-haspopup="dialog"><span class="i" aria-hidden="true">🚨</span>Alarm</a>`}
$("rama_dol").addEventListener("click",e=>{const a=e.target.closest("a");if(!a)return;
 if(a.id==="rama_alarm_przycisk"){e.preventDefault();alarm(true);return}
 if(a.dataset.krok&&MK){e.preventDefault();const k=MK.k+ +a.dataset.krok;
  if(k<0)wyjdzModul(MK.sec.id);else if(k>=MK.n){ukoncz(MK.sec.id);wyjdzModul(MK.sec.id)}else pokazKrok(MK.sec,k)}});
/* ── Alarm ── */
let alarmPowrot=null;function alarm(v){const a=$("rama_alarm");if(v){alarmPowrot=document.activeElement;a.hidden=false;$("rama_alarm_t").focus()}else{a.hidden=true;try{alarmPowrot&&alarmPowrot.focus()}catch(e){}}}
$("rama_alarm").addEventListener("click",e=>{if(e.target===e.currentTarget||e.target.closest(".zamknij"))alarm(false)});
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&!$("rama_alarm").hidden)alarm(false)});
/* ── konto, programy, dokumenty ── */
document.addEventListener("click",e=>{const a=e.target.closest&&e.target.closest("a");if(!a)return;
 if(a.id==="rama_wyloguj"){e.preventDefault();try{sessionStorage.clear()}catch(x){}wpis("WYLOGOWANIE");if(P)P.wyloguj();else location.replace(location.pathname)}
 else if(a.id==="rama_zmien"){e.preventDefault();wpis("ZMIANA_OSOBY");if(P)P.zmienOsobe()}
 else if(a.dataset.program){LS.set("rama_program",a.dataset.program)}
 else if(a.dataset.ukoncz){ukoncz(a.dataset.ukoncz)}});
function koniecDokumentu(sec){let k=sec.querySelector(":scope>.rama_koniec");const w=skad(sec.id);const z=w&&/^#temat\//.test(w);
 if(!z){if(k)k.hidden=true;return}if(!k){k=document.createElement("div");k.className="rama_koniec";sec.appendChild(k)}k.hidden=false;
 k.innerHTML=`<a class="btn glowny" href="${H(w)}" data-ukoncz="${H(sec.id)}">${H(N.DOKUMENT_KONIEC)}</a>`}
function uwagaTestu(sec){let u=$("rama_test_uwaga");const ms=modulyProg(program()),d=ukonczone(),zost=ms.filter(m=>!d.has(m));
 if(!zost.length){if(u)u.remove();return}if(!u){u=document.createElement("div");u.id="rama_test_uwaga";u.className="uwaga-pasek";sec.insertBefore(u,sec.firstChild)}
 u.innerHTML=`<span>${H(F(N.TEST_UWAGA,{n:zost.length,m:ms.length}))}</span><a href="#szkolenie">Przejdź do szkolenia</a>`}
/* ── rysowanie ekranu po każdej zmianie adresu ── */
function rysuj(){try{if(P)P.adres(location.hash)}catch(e){}const cz=decodeURIComponent((location.hash||"").slice(1)).split("/");
 /* część Zarządzanie tylko w trybie podglądu: inny adres #zarzadzanie lub ekran tej części wraca do ekranu startowego (kontrola całości, usterka B, 21.11.2026) */
 if(rola!=="PODGLAD"&&(["bhp","sprawy","zarzadzanie"].includes(cz[0])||["ZARZADZANIE","SPRAWY"].includes(R.cz[cz[0]]))){location.replace("#"+start());return}
 if(cz[0]==="zarzadzanie"){location.replace("#"+start());return}/* dawny adres części Zarządzanie */const s=document.querySelector("main section.on");const id=s?s.id:"";
 const main=$("main");main.removeAttribute("data-przewijanie");MK=null;let t="",w=null,ik="←",akt=null;
 if(id==="szkolenie"){t=ekranSzkolenie();akt="SZKOLENIE"}
 else if(id==="temat"){t=ekranTemat(cz);w="#szkolenie";akt="SZKOLENIE"}
 else if(id==="programy"){t=ekranProgramy();w="#szkolenie";akt="SZKOLENIE"}
 else if(id==="wiedza"){t=ekranWiedza();akt="WIEDZA"}
 else if(id==="bhp"){[t,w]=ekranBhp(cz);akt=cz[1]==="index"?"SPRAWY":"BHP";if(!t)return;pasek(t,w,ik);nawigacja("glowny",akt,cz[1]||"");if(!(cz.length>2&&cz[1]!=="ludzie"))window.scrollTo(0,0);return}
 else if(id==="sprawy"){t=ekranSprawy();akt="SPRAWY"}
 else if(id==="konto"){t=ekranKonto();akt="KONTO"}
 else if(/^m\d+$/.test(id)){const tm=SS.get("rama_temat");pasek(tyt(id),skad(id)||(tm?`#temat/${tm.pk}/${tm.nr}`:"#szkolenie"),"✕");wejdzModul(s,cz);return}
 else if(id){t=tyt(id);w=rodzic(id);akt={ZARZADZANIE:"BHP"}[R.cz[id]]||R.cz[id]||null;main.setAttribute("data-przewijanie",R.przew[id]||"dokument");
  if(id==="test")uwagaTestu(s);else koniecDokumentu(s)}
 pasek(t,w,ik);nawigacja("glowny",akt);window.scrollTo(0,0)}
addEventListener("hashchange",rysuj);/* bez popstate: przychodzi przed hashchange, gdy kurs jeszcze nie przełączył sekcji */
if(!location.hash||location.hash==="#"+start()){try{history.replaceState(history.state,"","#"+start())}catch(e){}if(typeof route==="function")route()}
rysuj();if(P)try{P.adres(location.hash)}catch(e){}
/* przeglądarka przewija do elementu o identyfikatorze z adresu (sekcja pod paskiem); ekran zawsze od góry */
addEventListener("load",()=>setTimeout(()=>{if(scrollY)window.scrollTo(0,0)},0));
})();</script>'''


def wstaw(doc, tryb):
    U, kafle, prog, obiekt = dane()
    sekcje = re.findall(r'<section id="([^"]+)"', doc)
    assert not set(EKRANY) & set(sekcje) and 'kafle' not in sekcje, 'STOP rama: rama już wstawiona'
    pj = _projekt()
    uklad = {r['sekcja']: r for r in pj.execute('select * from sekcja_ukladu order by czesc, kolejnosc')}
    modt = {r['modul']: r for r in pj.execute("select m.*, g.nazwa grupa_nazwa from modul_tytul m join grupa_tresci g on g.grupa=m.grupa where m.stan='PRZYJETY' order by m.kolejnosc")}
    tem_et = {(r['program'], r['nr']): r['etykieta'] for r in pj.execute('select * from temat_etykieta')}
    paleta = dict(pj.execute('select token, kolor from paleta_token'))
    N = napisy(pj)
    wyjatki = {r[0] for r in pj.execute('select wartosc from przewijanie_wyjatek')}
    for k, v in paleta.items():
        assert re.fullmatch(r'[a-z_]+', k) and re.fullmatch(r'#[0-9a-f]{6}', v), f'STOP rama: token palety {k}={v}'
    # sekcje obiektu (fragmenty części zarządzania BHP) – tylko na /pelny/
    obiekt_id = {fr: sid for fr, sid, _t, _n in obiekt}
    man = {x['fragment']: x for x in json.load(open(MANIFEST_SYSTEMU, encoding='utf8'))['pliki']} if os.path.exists(MANIFEST_SYSTEMU) else {}
    # każda sekcja strony ma miejsce w układzie (sekcja_ukladu, modul_tytul albo fragment obiektu); inaczej STOP
    znane = set(uklad) | set(modt) | set(obiekt_id.values())
    brak = [s for s in sekcje if s not in znane]
    assert not brak, f'STOP rama: sekcje strony bez miejsca w układzie (sekcja_ukladu/modul_tytul): {brak}'
    # tytuły (bez numerów, KS-15): moduły z modul_tytul, reszta z sekcja_ukladu, obiekt z MANIFEST
    tyt = {s: uklad[s]['etykieta'] for s in uklad}
    tyt.update({m: r['tytul_proponowany'] for m, r in modt.items()})
    cz_sek = {s: uklad[s]['czesc'] for s in uklad}
    for fr, sid in obiekt_id.items():
        if fr in man:
            tyt[sid] = man[fr]['kafel']
        cz_sek[sid] = 'WIEDZA'
    for m in modt:
        cz_sek.setdefault(m, 'SZKOLENIE')
    rodzic = {s: RODZIC[c] for s, c in cz_sek.items() if c in RODZIC}
    rodzic['test'] = '#szkolenie'
    for m in ('kartyryzyka', 'karty', 'soi'):
        rodzic[m] = '#wiedza'
    przew = {s: PRZEWIJANIE[c] for s, c in cz_sek.items() if c in PRZEWIJANIE}
    if 'obiekt_plan' in sekcje:
        przew['obiekt_plan'] = 'mapa'
    assert set(przew.values()) | {'dokument'} <= wyjatki, f'STOP rama: wyjątek przewijania spoza listy N-02: {set(przew.values()) - wyjatki}'
    # programy szkoleń (D-11): tematy z program_szkolenia, etykiety od 1 z temat_etykieta, moduły z moduly_kursu
    progr = {}
    for wym, sek, dop in PROGRAMY:
        assert sek in uklad, f'STOP rama: brak sekcji {sek} w sekcja_ukladu'
        tem = []
        for w_id, nr, temat, mod in prog:
            if w_id != wym:
                continue
            assert (wym, nr) in tem_et, f'STOP D-11: temat {wym} {nr} bez etykiety w temat_etykieta'
            ms = sorted(_moduly(mod, modt), key=lambda m: modt[m]['kolejnosc'])
            brak_m = [m for m in ms if m not in sekcje]
            assert not brak_m, f'STOP rama: program {wym} temat {nr} wskazuje moduły nieobecne na stronie {tryb}: {brak_m}'
            tem.append({'nr': nr, 't': tem_et[(wym, nr)], 'pelny': temat, 'm': ms})
        assert tem and [t['nr'] for t in tem] == list(range(1, len(tem) + 1)), f'STOP D-11: program {wym} bez tematów 1..N'
        progr[wym] = {'t': uklad[sek]['etykieta'] + dop, 'tem': tem}
    # Wiedza BHP: wiersze układu WIEDZA; opis z kafli kursu albo z MANIFEST części zarządzania BHP (kafel_opis)
    opis_k = {s: (o, r) for _k, _n, o, s, r in kafle}
    IK = {'kartyryzyka': '⚠️', 'karty': '🧪', 'soi': '🧤', 'strefy': '🦺', 'mapa': '🗺️', 'pomieszczenia': '🚪', 'roztwory': '⚗️'}
    wiedza = []
    for s, r in sorted(((s, r) for s, r in uklad.items() if r['czesc'] == 'WIEDZA'), key=lambda x: x[1]['kolejnosc']):
        rr = ['PODGLAD'] if r['rola'] == 'PODGLAD' else ['PRACOWNIK', 'PODGLAD']
        if s in WIEDZA_FRAGMENT:
            frs = [WIEDZA_FRAGMENT[s]] + (['pomieszczenia'] if s == 'mapa' else [])
            for fr in frs:
                if fr in man and obiekt_id.get(fr) in sekcje:
                    wiedza.append({'id': obiekt_id[fr], 't': r['etykieta'] if fr == WIEDZA_FRAGMENT[s] else man[fr]['kafel'],
                                   'o': man[fr].get('kafel_opis', ''), 'role': man[fr].get('role', rr), 'ik': IK.get(fr if fr == 'pomieszczenia' else s, '📄')})
            continue
        if s in sekcje:
            wiedza.append({'id': s, 't': r['etykieta'], 'o': opis_k.get(s, ('', ''))[0], 'role': rr, 'ik': IK.get(s, '📄')})
    dubel = {obiekt_id.get(fr) for fr in BHP_DUBLE_WIEDZY}
    for x in wiedza:
        x['bhp'] = x['id'] in dubel
    zarz = [{'id': s, 't': r['etykieta']} for s, r in sorted(uklad.items(), key=lambda x: x[1]['kolejnosc']) if r['czesc'] == 'ZARZADZANIE' and s in sekcje]
    sprawy = [{'id': s, 't': r['etykieta']} for s, r in sorted(uklad.items(), key=lambda x: x[1]['kolejnosc']) if r['czesc'] == 'SPRAWY' and s in sekcje]
    # BHP (etap 2): etykiety z sekcja_ukladu (część BHP, sekcje bhp_<id>), tytuły stron z MANIFEST części zarządzania BHP
    tyt_str = {x.get('plik_www', ''): x.get('tytul', '') for x in man.values()}
    bhp = [{'id': b, 'plik': pl, 't': uklad['bhp_' + b]['etykieta'], 'strona_t': tyt_str.get(pl) or uklad['bhp_' + b]['etykieta']}
           for b, pl in BHP_STRONY if 'bhp_' + b in uklad]
    bhp_ludzie = [{'plik': pl, 't': uklad['bhp_' + pl[:-5]]['etykieta']} for pl in BHP_LUDZIE_STRONY if 'bhp_' + pl[:-5] in uklad]
    sprawy += [{'h': '#bhp/' + s[len('bhp_'):].replace('_', '/'), 't': r['etykieta']}
               for s, r in sorted(uklad.items(), key=lambda x: x[1]['kolejnosc']) if r['czesc'] == 'SPRAWY' and s.startswith('bhp_')]
    if tryb == 'pracownik':
        zarz, sprawy, bhp, bhp_ludzie = [], [], [], []  # wersja dla pracowników: bez części BHP i Moje sprawy (usterka B kontroli całości, 21.11.2026)
    opisy = [{'id': s, 't': uklad[s]['etykieta']} for s in ('start', 'szkwstepne', 'szkokresowe') if s in uklad]
    # Konto (W-12): O aplikacji, Zmień osobę, Wyloguj; Ochrona danych na końcu (STOPKA)
    assert uklad['rodo']['czesc'] == 'KONTO' and uklad['rodo']['polozenie'] == 'STOPKA', 'STOP W-12: ochrona danych poza stopką Konta'
    konto = [{'id': 'start', 't': uklad['oaplikacji']['etykieta'], 'ik': 'ℹ️'},
             {'akcja': 'rama_zmien', 't': U['RAMA_ZMIEN_OSOBE'], 'ik': '🔁'},
             {'akcja': 'rama_wyloguj', 't': U['RAMA_WYLOGUJ'], 'ik': '⏻'},
             {'id': 'rodo', 't': uklad['rodo']['etykieta'], 'ik': '🔒'}]
    czesci = {'SZKOLENIE': 'Szkolenie', 'WIEDZA': 'Wiedza BHP', 'BHP': 'BHP', 'SPRAWY': 'Moje sprawy', 'KONTO': 'Konto'}
    nawig = [{'id': 'szkolenie', 'cz': 'SZKOLENIE', 'ik': '📘', 't': czesci['SZKOLENIE'], 'rola': ['PRACOWNIK', 'PODGLAD']},
             {'id': 'wiedza', 'cz': 'WIEDZA', 'ik': '📚', 't': czesci['WIEDZA'], 'krotko': 'Wiedza', 'rola': ['PRACOWNIK', 'PODGLAD']},
             {'id': 'bhp', 'cz': 'BHP', 'ik': '🦺', 't': czesci['BHP'], 'rola': ['PODGLAD'] if bhp else []},
             {'id': 'sprawy', 'cz': 'SPRAWY', 'ik': '📋', 't': czesci['SPRAWY'], 'krotko': 'Sprawy', 'rola': ['PODGLAD'] if sprawy else []},
             {'id': 'konto', 'cz': 'KONTO', 'ik': '👤', 't': czesci['KONTO'], 'rola': ['PRACOWNIK', 'PODGLAD']}]
    R = {'nazwa': U['RAMA_NAZWA'], 'prog': progr, 'domyslny': {'kier': 'OKR_KIER', 'prac': 'OKR_CURL_2026_11', 'brak': 'INSTR_OGOLNY'},
         'tyt': tyt, 'cz': cz_sek, 'rodzic': rodzic, 'przew': przew, 'grupa': {m: r['grupa_nazwa'] for m, r in modt.items()},
         'wiedza': wiedza, 'zarz': zarz, 'bhp': bhp, 'bhp_ludzie': bhp_ludzie, 'sprawy': sprawy, 'opisy': opisy, 'konto': konto, 'czesci': czesci, 'nawig': nawig, 'ekrany': list(EKRANY),
         'wstep': 'Wprowadzenie', 'slowa': 70, 'napis': N,
         'dziennik': U['RAMA_DZIENNIK_WEJSC'] == '1' or (bool(os.environ.get('PINY_WWW_TEST')) and os.environ.get('RAMA_DZIENNIK_WEJSC_TEST') == '1')}
    # RAMA_DZIENNIK_WEJSC_TEST działa tylko w budowie testowej (PINY_WWW_TEST, PIN-y TEST<KOD>): test zachowania dziennika wejść R9
    logo = logo_img(28, U['RAMA_LOGO'])
    # Alarm: numery ogólnopolskie; adres obiektu, miejsce zbiórki i numery wewnętrzne tylko z bazy kadr.
    # TS 20.11.2026 10:13 (ZG-1120-1013-1): bez widocznego „do uzupełnienia” – brak danej = wiersz pominięty,
    # a luka zostaje tylko w atrybucie data-brak (dane wewnętrzne, panel administracyjny)
    luki = []
    def _et(k, w=None):   # wartość z bazy kadr; brak = pusty wiersz + kod luki
        e = N[k].split(': ', 1)[0].strip()   # wzór = sama etykieta (projekt_strony, dopisek 038) albo „etykieta: …”
        if not w: luki.append(k); return ''
        return f'<p><b>{_e(e)}:</b> {_e(w)}</p>'
    zg_e, zg_t = N['ALARM_ZGLOSZENIE'].split(': ', 1)
    zg_t = zg_t.replace('{adres obiektu}', 'obiektu')   # sam adres osobno: ALARM_ADRES
    assert '{' not in zg_t, 'STOP rama: nieznane pole w ALARM_ZGLOSZENIE'
    pp_e = N['ALARM_PIERWSZA_POMOC'].split(': ', 1)[0].strip()
    # Dane Alarmu wyłącznie z części kadr (adm.sqlite, panel ustawień TS 20.11.2026 03:06; reguły TF-01, RO-01):
    # numery v_dane_alarmowe_aktualne, osoby pierwszej pomocy v_rola_aktualna (rola PIERWSZA_POMOC)
    ka = polacz('KADRY')
    dal = ka.execute('select kod, rodzaj, wartosc, rola, osoba from v_dane_alarmowe_aktualne order by kolejnosc, kod').fetchall()
    pp_os = [x[0] for x in ka.execute("select osoba from v_rola_aktualna where rola='PIERWSZA_POMOC' order by od, kod_osoby").fetchall()]
    ka.close()
    tel = {k: w for k, rd, w, _r, _o in dal if rd == 'TELEFON'}
    # TS 20.11.2026 07:29: brak numeru albo osoby nie zatrzymuje budowy (uwaga po stronie kadr); od 10:13 bez widocznego napisu o braku
    tel_pp = next((w for k, rd, w, rl, _o in dal if rd == 'TELEFON' and rl == 'PIERWSZA_POMOC' and w), None)
    adr = {rd: w for k, rd, w, _r, _o in dal if rd in ('ADRES', 'ZBIORKA') and w}
    zadzwon = f'<i class="zadzwon" aria-hidden="true">{_e(N["ALARM_ZADZWON"])}</i>'
    def _tel(nr, nazwa, kl=''):
        if not nr:
            luki.append('TEL ' + nazwa); return ''
        nr = _e(nr); return f'<a class="tel{kl}" href="tel:{re.sub(r"[^0-9+]", "", nr)}" aria-label="{_e(N["ALARM_ZADZWON"][2:].strip())}: {nr} – {_e(nazwa)}"><b>{nr}</b><span>{_e(nazwa)}</span>{zadzwon}</a>'
    # pierwsza pomoc: z przyciskiem tylko, gdy kadry mają numer (TELEFON z rolą PIERWSZA_POMOC); bez numeru wiersz bez przycisku
    alarm = ('<div class="arkusz" id="rama_alarm" hidden role="dialog" aria-modal="true" aria-labelledby="rama_alarm_t"><div class="panel">'
             '<h2 id="rama_alarm_t" tabindex="-1">🚨 Alarm</h2>'
             + _tel(tel.get('TEL_112'), N['ALARM_112'], ' t112') + _tel(tel.get('TEL_998'), 'Straż pożarna') + _tel(tel.get('TEL_999'), 'Pogotowie ratunkowe')
             + (f'<a class="tel wewn" href="tel:{_e(re.sub(r"[^0-9+]", "", tel_pp))}"><b>{_e(pp_e)}</b><span>{_e(", ".join(pp_os))}<small>{_e(tel_pp)}</small></span>{zadzwon}</a>'
                if tel_pp else (f'<div class="tel wewn"><b>{_e(pp_e)}</b><span>{_e(", ".join(pp_os))}</span></div>' if pp_os else ''))
             + f'<div class="adres"><p><b>{_e(zg_e)}:</b> {_e(zg_t)}</p>{_et("ALARM_ADRES", adr.get("ADRES"))}{_et("ALARM_ZBIORKA", adr.get("ZBIORKA"))}</div>'
             '<button type="button" class="zamknij">Zamknij</button></div></div>')
    if not tel_pp: luki.append('ALARM_PIERWSZA_POMOC numer')
    if not pp_os: luki.append('ALARM_PIERWSZA_POMOC osoby')
    if luki: alarm = alarm.replace('id="rama_alarm"', f'id="rama_alarm" data-brak="{_e("; ".join(luki))}"', 1)
    gora = (f'<header class="pasek" id="rama" data-rama="{_e(tryb)}"><a class="ikona" id="rama_wstecz" href="#szkolenie" hidden>←</a>{logo}'
            f'<span class="tytul" id="rama_tytul"></span></header>'
            f'<nav class="dol" id="rama_dol" aria-label="{_e(U["RAMA_NAZWA"])}"></nav>{alarm}')
    ekr = ''.join(f'<section id="{s}" class="ekran_ramy" data-title="{_e(s)}"></section>\n' for s in EKRANY)
    assert doc.count('<div class="wrap">') == 1, 'STOP rama: brak jednego <div class="wrap"> w treści strony'
    doc = doc.replace('<div class="wrap">', gora + '<div class="wrap">', 1)
    assert doc.count('<section id="start"') == 1, 'STOP rama: brak sekcji start'
    doc = doc.replace('<section id="start"', ekr + '<section id="start"', 1)
    # ekran startowy = Szkolenie; adres kroku modułu #m5/2/3 → sekcja m5
    stary = 'let id=(location.hash||"#start").slice(1);\n  if(!sections.some(s=>s.id===id))id="start";'
    assert doc.count(stary) == 1, 'STOP rama: zmieniony kod wyboru sekcji (route)'
    doc = doc.replace(stary, 'let id=(location.hash||"#szkolenie").slice(1).split("/")[0];\n  if(!sections.some(s=>s.id===id))id="szkolenie";', 1)
    dane_js = '<script>window.RAMA_APLIKACJI=' + json.dumps(R, ensure_ascii=False).replace('</', '<\\/') + ';</script>'
    assert doc.count('</head>') >= 1 and doc.rfind('</body>') > 0
    # jeden jasny motyw: reguły dla ustawienia ciemnego w treści nigdy nie działają (STOP, gdy któraś zostanie)
    doc = re.sub(r'@media\s*\(\s*prefers-color-scheme\s*:\s*dark\s*\)', '@media not all', doc)
    assert not re.search(r'prefers-color-scheme\s*:\s*dark', doc), 'STOP rama: zostało ustawienie ciemne'
    i = doc.index('</head>')
    # wejście musi mieć prawdziwy <head> na początku (kopia_samodzielna.py); w kurs_bhp_curl.html pierwsze </head> jest
    # w szablonie druku fullDoc i styl ramy trafiłby do wydruków (uwaga projektu 19.11.2026)
    assert 0 <= doc.find('<head>') < i < 4096 and '<script' not in doc[:i], 'STOP rama: pierwszy </head> nie jest nagłówkiem dokumentu'
    css = CSS.replace('__ZMIENNE__', ';'.join(f'--r-{k}:{v}' for k, v in sorted(paleta.items())))
    assert '__' not in re.sub(r'/\*.*?\*/', '', css), 'STOP rama: nieznany znacznik w stylu'
    doc = doc[:i] + css + doc[i:]
    j = doc.rfind('</body>'); doc = doc[:j] + dane_js + JS + doc[j:]
    return doc, {'ekrany': len(EKRANY), 'programy': {k: len(v['tem']) for k, v in progr.items()}, 'wiedza': len(wiedza), 'zarzadzanie': len(zarz), 'bhp': len(bhp), 'sprawy': len(sprawy)}

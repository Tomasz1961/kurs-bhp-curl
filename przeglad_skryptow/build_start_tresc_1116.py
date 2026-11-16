#!/usr/bin/env python3
"""Krok 11zz9 (16.11.2026): strona Start – najpierw treść, nazwiska dalej (TS 16.11.2026 20:12 i 20:16, decyzje 146–148, 152).
TS: „jak się otworzy, są nazwiska. Czy to jest lista obecności, czy istotą jest treść … co gdzie się dzieje, na czym polegają te
szkolenia, kto musi co odbyć, a dopiero potem nazwiska” oraz „nie mówię, żeby przebudowywać wszystko … tylko żeby to usprawnić”.
Zmiany (bez przebudowy kursu; poprawka na gotowym pliku, po kroku 11zt):
 1) przed wyborem szkolenia blok „Czym jest CURL i czego uczy ten kurs” – opis obiektu słowami TS z 20:12 (części obiektu, GACP,
    droga jednokierunkowa, monitoring i ochrona, zezwolenie GIF bez numerów przepisów – te tylko z rejestru aktów) i pytania,
    na które odpowiada kurs, z odnośnikami do modułów, w których jest odpowiedź;
 2) karty szkoleń: przycisk „Rozpocznij szkolenie” prowadzi do szkolenia krok po kroku (dec. 144), nie do osobnego testu (dec. 145);
    zdanie wstępu zgodne z tym; „Tematy programu” → „Tematy w programie działu BHP” (to liczba tematów programu, nie modułów);
 3) stan wypełnionych testów z nazwiskami (TS 15.11 22:39, tylko prowadzący i podgląd) przeniesiony z kart na koniec strony Start,
    do bloku „Stan szkoleń w zespole” – pierwszy ekran bez nazwisk.
Idempotentne (bloki zastępowane w miejscu), bez LLM. Test: kontrola/test_start_tresc.js (pierwszy widok bez nazwisk, kolejność,
przycisk prowadzi do ścieżki). Zapis: decyzja_ts 148 → WDROZONE_W_PLIKU (kontrola D-148)."""
import re, sqlite3, os, sys
B = '/mnt/project-files/bhp'
P = sys.argv[1] if len(sys.argv) > 1 else f'{B}/kurs_online/kurs_bhp_curl.html'
h = open(P, encoding='utf-8').read(); h0 = h

TRESC = '''<!--START-TRESC-1116-->
<div class="sto">
<h3>Czym jest CURL i czego uczy ten kurs</h3>
<p>Centrum Uprawy Roślin Leczniczych IUNG-PIB w Sarnowie łączy dwie części: <b>uprawową</b>, w której konopie medyczne rosną w warunkach kontrolowanych, oraz <b>pozbiorową</b>, w której surowiec zielarski jest suszony, trymowany i pakowany zgodnie z dobrą praktyką uprawy i zbioru (GACP) Europejskiej Agencji Leków.</p>
<ul class="sto-cz">
<li><b>Część uprawowa:</b> 7 boksów uprawowych, mnożarka i klonownik.</li>
<li><b>Część pozbiorowa:</b> pomieszczenia czyste oddzielone śluzami – trymowanie, suszenie, pakowanie i magazynowanie.</li>
<li><b>Magazyny:</b> magazyn surowca zielarskiego i magazyn środków do produkcji.</li>
<li><b>Część biurowa i socjalna.</b></li>
</ul>
<p>Rośliny, ludzie i materiały poruszają się jedną drogą, w jednym kierunku, z zachowaniem warunków higienicznych i ochrony roślin. Każde zagrożenie jest przypisane do miejsca i czynności, przy których występuje, a do tych miejsc – instrukcje, procedury, karty charakterystyki, potrzebny sprzęt i oznakowanie. Obiekt jest objęty stałym monitoringiem wizyjnym i ochroną fizyczną, a uprawa odbywa się na podstawie zezwolenia Głównego Inspektora Farmaceutycznego.</p>
<h4>Na jakie pytania odpowiada kurs</h4>
<ol class="sto-pyt">
<li><b>Gdzie jestem?</b> Strefy obiektu i droga przez szatnie i śluzy – <a href="#m8">moduł 8</a>.</li>
<li><b>Co robię i co mi grozi?</b> Karta oceny ryzyka Twojego stanowiska – <a href="#kartyryzyka">Karty oceny ryzyka</a>; zagrożenia – <a href="#m2">moduły 2–7</a>.</li>
<li><b>Skąd się dowiem?</b> Karty charakterystyki – <a href="#karty">Substancje chemiczne</a>; środki ochrony – <a href="#soi">ŚOI</a>.</li>
<li><b>Jak postępować, gdy coś się dzieje?</b> Pożar – <a href="#m9">moduł 9</a>; pierwsza pomoc – <a href="#m10">moduł 10</a>.</li>
<li><b>Jak to udokumentować?</b> Zgłoszenie wypadku i zdarzenia – <a href="#m11">moduł 11</a>.</li>
</ol>
</div>
<style>.sto{margin:6px 0 20px}.sto h3{margin:0 0 6px}.sto h4{margin:14px 0 6px}.sto-cz,.sto-pyt{margin:6px 0 10px;padding-left:22px}.sto-cz li,.sto-pyt li{margin:3px 0}</style>
<!--/START-TRESC-1116-->
'''
h = re.sub(r'<!--START-TRESC-1116-->.*?<!--/START-TRESC-1116-->\n?', '', h, flags=re.S)
assert h.count('<!--WYBOR-SZK-START-->') == 1, 'STOP 11zz9: brak bloku wyboru szkolenia (krok 11zw2)'
h = h.replace('<!--WYBOR-SZK-START-->', TRESC + '<!--WYBOR-SZK-START-->')

# 2) karty szkoleń
WST_STARE = ('Każde szkolenie ma własny zakres i własny test. Wybierz szkolenie, przeczytaj moduły z jego programu, a potem kliknij „Rozwiąż test” '
             'i wybierz swoje nazwisko. Wypełniony test zapisuje się automatycznie; zaświadczenie i sprawdzian z odpowiedziami są od razu gotowe do wydruku i podpisu.')
WST_NOWE = ('Wybierz szkolenie, które Cię dotyczy, i kliknij „Rozpocznij szkolenie”. Moduły przechodzisz po kolei: czytasz, potwierdzasz i odpowiadasz '
            'na pytania sprawdzające. Odpowiedzi ze wszystkich modułów dają wynik szkolenia; na jego podstawie otrzymujesz zaświadczenie do podpisu.')
h = h.replace(WST_STARE, WST_NOWE)
CEL = {'wstepne': '#szkwstepne', 'okresowe': '#szkokresowe', 'kierujacy': '#szkokresowe'}
for t, cel in CEL.items():
    h = h.replace(f'<button type="button" class="primary" data-szktest="{t}">Rozwiąż test</button>',
                  f'<button type="button" class="primary" data-sto-start="{cel}" onclick="location.hash=\'{cel}\'">Rozpocznij szkolenie</button>')
h = h.replace('<dt>Tematy programu</dt>', '<dt>Tematy w programie działu BHP</dt>')

# 3) stan z nazwiskami: z kart na koniec strony Start
i = h.find('<!--WYBOR-SZK-START-->'); j = h.find('<!--WYBOR-SZK-KONIEC-->', i)
blk = h[i:j]
blk = blk.replace('\n  <div class="wsz-stan" hidden></div>', '')
blk = blk.replace('el=c.querySelector(".wsz-stan")', 'el=document.querySelector(\'.wsz-stan-zesp[data-wsz="\'+pref+\'"]\')')
blk = blk.replace('document.querySelectorAll(".wsz-karta").forEach(c=>{const pref=c.dataset.wsz,el=',
                  'document.querySelectorAll(".wsz-karta").forEach(c=>{const pref=c.dataset.wsz;if(!document.querySelector(\'.wsz-stan-zesp[data-wsz="\'+pref+\'"]\'))return;const el=')
blk = re.sub(r'<p class="wsz-leg" hidden>.*?</p>\n', '', blk, flags=re.S)
blk = blk.replace('const lg=document.querySelector(".wsz-leg");if(lg)lg.hidden=!jest;return jest',
                  'const z=document.getElementById("sto_zespol");if(z)z.hidden=!jest;return jest')
h = h[:i] + blk + h[j:]
NAZWY = re.findall(r'<article class="wsz-karta[^"]*" data-wsz="([^"]+)"', blk)
assert len(NAZWY) == 3, 'STOP 11zz9: oczekiwano 3 kart szkoleń'
ZESP = ('<!--START-ZESPOL-1116-->\n<div id="sto_zespol" class="sto-zesp" hidden>\n<h3>Stan szkoleń w zespole</h3>\n'
        '<p class="wsz-leg"><span class="wsz-b wsz-b-cz">wypełniony – czeka na podpis</span> szkolenie zakończone, dokument do podpisu uczestnika; '
        '<span class="wsz-b wsz-b-ok">podpisany</span> podpisany skan przesłany i zatwierdzony.</p>\n'
        + ''.join(f'<h4>{n}</h4><div class="wsz-stan wsz-stan-zesp" data-wsz="{n}" hidden></div>\n' for n in NAZWY)
        + '</div>\n<!--/START-ZESPOL-1116-->\n')
h = re.sub(r'<!--START-ZESPOL-1116-->.*?<!--/START-ZESPOL-1116-->\n?', '', h, flags=re.S)
s0 = h.find('<section id="start"'); s1 = h.find('</section>', s0)
assert s0 > 0 and s1 > s0, 'STOP 11zz9: brak sekcji Start'
h = h[:s1] + ZESP + h[s1:]

# kontrole po kroku
st = h[h.find('<section id="start"'):h.find('</section>', h.find('<section id="start"'))]
assert st.find('<!--START-TRESC-1116-->') < st.find('<!--WYBOR-SZK-START-->') < st.find('<!--START-ZESPOL-1116-->'), 'STOP 11zz9: kolejność Start'
assert 'Rozwiąż test' not in st and st.count('data-sto-start=') == 3, 'STOP 11zz9: przyciski kart'
assert 'class="wsz-stan" hidden' not in st, 'STOP 11zz9: stan z nazwiskami w karcie'
if h != h0: open(P, 'w', encoding='utf-8').write(h)
if len(sys.argv) <= 1:
    c = sqlite3.connect(os.environ.get('BHP_DB', f'{B}/bhp_rejestr.sqlite'))
    c.execute("update decyzja_ts set status='WDROZONE_W_PLIKU', wdrozenie='krok 11zz9 build_start_tresc_1116.py (Start: treść, potem szkolenia, nazwiska na końcu); kontrola D-148, test test_start_tresc.js' where id=148")
    c.commit(); c.close()
print(f'11zz9 Start – treść przed nazwiskami: kurs {"zmieniony" if h != h0 else "bez zmian"} | karty {len(NAZWY)}')

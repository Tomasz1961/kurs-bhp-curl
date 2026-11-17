#!/usr/bin/env python3
"""Testy negatywne testu strony Start (test_start_tresc.js): wstawia na początek sekcji #start nazwisko z danych
w pięciu układach i sprawdza, że test zgłasza błąd tylko wtedy, gdy nazwisko jest widoczne na pierwszych ekranach.
Użycie: python3 test_start_tresc_negatywny.py KURS.html kurs_admin_dane.json   (uwagi Copilota do PR #18)"""
import json, os, re, subprocess, sys, tempfile
K, AD = sys.argv[1:3]
d = json.load(open(AD, encoding='utf8')); p = d['prac-data']; p = json.loads(p) if isinstance(p, str) else p
n = p['ludzie'][0]['n']; a, b = n.split()[0], ' '.join(n.split()[1:])
h = open(K, encoding='utf8').read(); i = re.search(r'<section[^>]*id="start"[^>]*>', h).end()
PRZYPADKI = {  # nazwa: (wstawka, czy test ma zgłosić błąd)
    'ukryte': (f'<p>Wstęp<span hidden>{n}</span></p>', False),
    'dwa_odlegle_bloki': (f'<p>{a} </p><p style="margin-top:9000px">{b}</p>', False),
    'inline': (f'<p>Wstęp <b>{a}</b> {b}</p>', True),
    'nowa_linia': (f'<p><span>{a}</span>\n<span>{b}</span></p>', True),
    'flex_gap': (f'<div style="display:flex;gap:8px"><div>{a}</div><div>{b}</div></div>', True),
    'br': (f'<p><span>{a}</span><br><span>{b}</span></p>', True),
    'slowo_podzielone_inline': (f'<p>{a} {b[:2]}<b>{b[2:]}</b></p>', True),
    'blok_wewnatrz_nazwiska': (f'<div>{a} {b[:2]}<div>inny tekst</div>{b[2:]}</div>', False),
    'czlony_w_roznych_akapitach': (f'<p>Wprowadzenie: {a}</p><p>Kontakt: {b}</p>', False),
    'display_contents': (f'<span style="display:contents">{n}<small> 2026</small></span>', True)}
zle = []
with tempfile.TemporaryDirectory() as td:
    for nazwa, (w, blad) in PRZYPADKI.items():
        f = os.path.join(td, nazwa + '.html'); open(f, 'w', encoding='utf8').write(h[:i] + w + h[i:])
        r = subprocess.run(['node', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_start_tresc.js'), f, AD], capture_output=True, text=True, timeout=600)
        # wynik z JSON: wykrycie = wstawione nazwisko w „nazwiskaWidoczne” obu szerokości; inne błędy testu = niepowodzenie (uwaga Copilota)
        try: W = json.loads(r.stdout[r.stdout.index('{'):])
        except Exception: zle.append(nazwa + ' (brak wyniku JSON)'); continue
        wykr = [n in (W.get(k) or {}).get('nazwiskaWidoczne', []) for k in ('1366', '390')]
        # spójność: kod wyjścia, WYNIK, lista nazwisk i błędy muszą odpowiadać oczekiwaniu (uwaga Copilota)
        if blad: inne = [e for e in W.get('bledy', []) if 'nazwiska na pierwszych ekranach' not in e]
        else: inne = list(W.get('bledy', []))
        if inne: zle.append(nazwa + ' (inne błędy: ' + '; '.join(inne)[:200] + ')'); continue
        if len(set(wykr)) != 1: zle.append(nazwa + ' (różny wynik dla szerokości)'); continue
        wykryto = wykr[0]
        spojny = (r.returncode != 0) == wykryto and (W.get('WYNIK') == 'BŁĄD') == wykryto
        if not spojny: zle.append(nazwa + f' (niespójny wynik: kod {r.returncode}, WYNIK {W.get("WYNIK")}, wykryto {wykryto})'); continue
        print(f'{nazwa}: oczekiwano {"wykrycia" if blad else "braku wykrycia"}, wynik {"wykryto" if wykryto else "nie wykryto"}')
        if wykryto != blad: zle.append(nazwa)
print('WYNIK:', 'BŁĄD ' + ','.join(zle) if zle else 'OK'); sys.exit(1 if zle else 0)

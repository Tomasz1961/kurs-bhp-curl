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
    'flex_gap': (f'<div style="display:flex;gap:8px"><div>{a}</div><div>{b}</div></div>', True)}
zle = []
with tempfile.TemporaryDirectory() as td:
    for nazwa, (w, blad) in PRZYPADKI.items():
        f = os.path.join(td, nazwa + '.html'); open(f, 'w', encoding='utf8').write(h[:i] + w + h[i:])
        r = subprocess.run(['node', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_start_tresc.js'), f, AD], capture_output=True, text=True, timeout=600)
        wykryto = r.returncode != 0
        print(f'{nazwa}: oczekiwano {"BŁĄD" if blad else "OK"}, wynik {"BŁĄD" if wykryto else "OK"}')
        if wykryto != blad: zle.append(nazwa)
print('WYNIK:', 'BŁĄD ' + ','.join(zle) if zle else 'OK'); sys.exit(1 if zle else 0)

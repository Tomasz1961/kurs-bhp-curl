#!/usr/bin/env python3
"""Wspólny sprawdzacz języka (ten sam kod lokalnie i w GitHub Actions; dec. 128).
Użycie: python3 sprawdz_jezyk.py <teksty.json z render_zakladki.js> <jezyk_lista.json> [--pokaz]
jezyk_lista.json = {"zakazane": [[wzorzec, powod], ...], "wyjatki": [wzorzec, ...]} – eksport z bhp_rejestr
(jezyk_zakazany, jezyk_wyjatek) przez eksport_jezyk_lista.py. Wynik: liczba trafień i skrót SHA-256 wejść; kod 1 przy trafieniu
albo błędzie skryptu strony."""
import hashlib, json, re, sys

def trafienia(teksty, zak, wyj):
    out = []
    for zk, t in teksty.items():
        if zk.startswith('_bledy'): continue
        for w in wyj: t = re.sub(w, ' ', t, flags=re.I)
        for wz, _ in zak:
            for m in re.finditer(wz, t, flags=re.I):
                out.append((zk, wz, t[max(0, m.start()-50):m.end()+50].replace('\n', ' ')))
    return out

if __name__ == '__main__':
    tj, lj = sys.argv[1], sys.argv[2]
    teksty = json.load(open(tj, encoding='utf-8')); lista = json.load(open(lj, encoding='utf-8'))
    tr = trafienia(teksty, lista['zakazane'], lista['wyjatki'])
    bl = teksty.get('_bledy_strony', '')
    sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
    print(f'kontrola języka www: zakładek {len([k for k in teksty if not k.startswith("_")])} | trafień {len(tr)} | błędy skryptów {"tak" if bl else "nie"} | lista {sha(lj)}')
    if '--pokaz' in sys.argv or tr:
        for x in tr: print('  ', x[0], '|', x[1], '|', x[2])
    if bl: print('  błędy strony:', bl)
    sys.exit(1 if tr or bl else 0)

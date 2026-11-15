#!/usr/bin/env python3
"""Test negatywny kontroli odnośników (recenzja Copilota do PR #5, 15.11.2026): kontrola musi wykryć brakujący plik
w każdym z przypadków poniżej i przejść, gdy plik jest. Każdy przypadek w osobnym katalogu tymczasowym."""
import os, subprocess, sys, tempfile
K = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sprawdz_odnosniki.py')
PRZYPADKI = {
    'skrypt z src (pojedyncze cudzysłowy)': ("<script src='pliki/brak.js'></script>", 'pliki/brak.js'),
    'skrypt z src i treścią': ('<script src="pliki/brak2.js">var x=1;</script>', 'pliki/brak2.js'),
    'odnośnik w pojedynczych cudzysłowach': ("<a href='sds/brak.pdf'>PDF</a>", 'sds/brak.pdf'),
    'odnośnik bez cudzysłowów': ('<a href=sds/brak3.pdf>PDF</a>', 'sds/brak3.pdf'),
    'obraz bez cudzysłowów': ('<img src=obrazy/brak.png alt="">', 'obrazy/brak.png'),
    'arkusz stylów': ("<link rel=stylesheet href='styl/brak.css'>", 'styl/brak.css'),
    'odnośnik w tekście skryptu': ('<script>el.innerHTML=\'<a href="wzory/brak.docx">wzór</a>\'</script>', 'wzory/brak.docx'),
}
bledy = 0
for nazwa, (znacznik, plik) in PRZYPADKI.items():
    with tempfile.TemporaryDirectory() as d:
        strona = os.path.join(d, 'index.html')
        open(strona, 'w', encoding='utf8').write(f'<!doctype html><html><body>{znacznik}<a href="https://example.org/x.pdf">z</a><a href="#a">a</a></body></html>')
        env = dict(os.environ, MIN_SDS='0')
        bez = subprocess.run([sys.executable, K, strona, d], capture_output=True, text=True, env=env)
        os.makedirs(os.path.dirname(os.path.join(d, plik)), exist_ok=True); open(os.path.join(d, plik), 'w').write('x')
        z = subprocess.run([sys.executable, K, strona, d], capture_output=True, text=True, env=env)
        ok = bez.returncode == 1 and f'BRAK: {plik}' in bez.stdout and z.returncode == 0
        bledy += not ok
        print(('OK   ' if ok else 'BŁĄD ') + f'{nazwa}: bez pliku → kod {bez.returncode}, z plikiem → kod {z.returncode}')
print(f'test negatywny odnośników: przypadków {len(PRZYPADKI)}, niewykrytych {bledy}')
sys.exit(1 if bledy else 0)

#!/usr/bin/env python3
"""Sprawdzenie plików przed publikacją strony (polecenie z 19.11.2026: karty charakterystyki tylko po zalogowaniu;
uwaga przeglądu #31: odrzucić dowiązania symboliczne, bo publikacja je rozwija).
Użycie: sprawdz_publikacje.py KATALOG   – kod 1, gdy w katalogu jest dowiązanie symboliczne, plik spoza listy
                                          dozwolonych albo jawny PDF;
        sprawdz_publikacje.py --negatywny – test negatywny: podłożone dowiązania (do pliku PDF i do katalogu) oraz jawny PDF
                                          muszą być wykryte, a poprawny zestaw musi przejść."""
import os, re, sys, tempfile
W = r'(?:wersja-\d{4}-\d\d-\d\d/)?'
D = re.compile(W + r'(?:(?:pelny|pracownik|pelny/aplikacja)/)?zapis\.json|\.nojekyll|index\.html|' + W
               + r'(?:pelny|pracownik|pelny/aplikacja)/index\.html|' + W + r'(?:pelny|pracownik)/sds/[A-Za-z0-9_.-]+\.bin|'
               + W + r'przypomnienia/[a-z_]+/index\.html')   # 26.11.2026: strony przypomnień obszarów (jak W-07 w teście wydania)
ZASZ = re.compile(rb'const D=\{s:"[A-Za-z0-9+/=]+",i:"[A-Za-z0-9+/=]+",n:\d+,c:"[A-Za-z0-9+/=]+"\}')   # ładowacz szyfru AES-GCM


def sprawdz(kat):
    zle = []
    for k, katalogi, pliki in os.walk(kat):  # os.walk nie wchodzi w dowiązane katalogi, więc sprawdzamy je jawnie
        for n in katalogi + pliki:
            p = os.path.join(k, n); r = os.path.relpath(p, kat).replace(os.sep, '/')
            if os.path.islink(p):
                zle.append(r + ': dowiązanie symboliczne')
            elif n in pliki:
                if not D.fullmatch(r):
                    zle.append(r + ': plik spoza listy dozwolonych')
                elif b'%PDF-' in open(p, 'rb').read(1024):
                    zle.append(r + ': jawny PDF')
                elif r.split('/')[-3:-2] == ['przypomnienia'] and not ZASZ.search(open(p, 'rb').read()):
                    zle.append(r + ': strona przypomnień bez szyfru')
    return zle


def negatywny():
    with tempfile.TemporaryDirectory() as T:
        dobry = os.path.join(T, 'dobry'); os.makedirs(f'{dobry}/pelny/sds')
        open(f'{dobry}/index.html', 'w').write('<html></html>'); open(f'{dobry}/pelny/sds/a.pdf.bin', 'wb').write(b'\x00' * 64)
        os.makedirs(f'{dobry}/przypomnienia/biurowa')
        open(f'{dobry}/przypomnienia/biurowa/index.html', 'w').write('<script>const D={s:"QQ==",i:"QQ==",n:600000,c:"QQ=="};</script>')
        open(f'{T}/jawna.pdf', 'wb').write(b'%PDF-1.4 jawna'); os.makedirs(f'{T}/poza/sds'); open(f'{T}/poza/sds/b.pdf', 'wb').write(b'%PDF-1.4')
        przypadki = {
            'dowiązanie do jawnego PDF udające kartę zaszyfrowaną': lambda d: os.symlink(f'{T}/jawna.pdf', f'{d}/pelny/sds/x.pdf.bin'),
            'dowiązanie do katalogu z jawnymi kartami': lambda d: os.symlink(f'{T}/poza/sds', f'{d}/pracownik'),
            'jawny PDF udający kartę zaszyfrowaną': lambda d: open(f'{d}/pelny/sds/y.pdf.bin', 'wb').write(b'%PDF-1.4'),
            'jawna strona przypomnień': lambda d: (os.makedirs(f'{d}/przypomnienia/biurowa'),
                                                   open(f'{d}/przypomnienia/biurowa/index.html', 'w').write('<p>jawna treść</p>')),
        }
        bledy = 0
        if sprawdz(dobry):
            print('BŁĄD poprawny zestaw odrzucony:', sprawdz(dobry)); bledy += 1
        else:
            print('OK   poprawny zestaw przechodzi')
        for i, (opis, zepsuj) in enumerate(przypadki.items()):
            d = os.path.join(T, f'p{i}')
            os.makedirs(f'{d}/pelny/sds'); open(f'{d}/index.html', 'w').write('<html></html>')
            zepsuj(d); w = sprawdz(d)
            print(('OK   ' if w else 'BŁĄD ') + opis + (f' wykryte: {w}' if w else ' NIE wykryte')); bledy += not w
        print(f'test negatywny publikacji: przypadków {len(przypadki)}, niewykrytych {bledy}')
        return 1 if bledy else 0


if __name__ == '__main__':
    if sys.argv[1:] == ['--negatywny']:
        sys.exit(negatywny())
    zle = sprawdz(sys.argv[1])
    print('\n'.join(zle) or 'OK: tylko pliki dozwolone, bez dowiązań, żadnego jawnego PDF')
    sys.exit(1 if zle else 0)

# Propozycja etapu 2: BHP w jednym oknie (bez wydania)

Decyzja TS 26.11.2026 19:30 UTC (etap 1 i 2, wątek „Przywróć spójny układ aplikacji GACP”, W-319/Z-380).
Ta gałąź niczego nie publikuje: strona idzie na serwer tylko z `main`, a pliki tu są wyłącznie do przeglądu.

## Co się zmienia w ramie aplikacji (`rama_aplikacji.py`, różnice w `rama_aplikacji.diff`)
- Jedno menu ramy: **Szkolenie, Wiedza BHP, BHP, Moje sprawy, Konto, Alarm**. Na komputerze pod „BHP” są od razu
  pozycje **Mapa obiektu, Środki ochrony, Pracownicy i dokumenty**. Na telefonie „BHP” otwiera listę tych trzech pozycji.
- Strony części zarządzania BHP (`/pelny/aplikacja/*.html`) są pokazywane wewnątrz ramy (ekran `#bhp/<strona>`):
  bez własnego paska „← Aplikacja CURL”, bez własnego menu i bez drugiego „Szkolenia”. Odnośniki między nimi zostają w ramie.
- „Pracownicy i dokumenty” to lista: strona Pracownicy, Szkolenia przeprowadzone i Dokumenty z części zarządzania BHP
  oraz dotychczasowe pozycje z „Zarządzania” w kursie (Pracownicy, Teczka osoby, Wyniki testów, Dokumenty szkoleń,
  Dokumentacja GACP, Dziennik dostępu, Archiwum).
- **Moje sprawy** (osobna pozycja, wyjęta z BHP): Sprawy do załatwienia i Najbliższe terminy. To jest ekran startowy osoby z podglądem.
- Dla osoby z podglądem „Wiedza BHP” nie powtarza mapy, pomieszczeń i stref (są w BHP). Wersja pracownika jest bez zmian.
- Dotychczasowy adres `#zarzadzanie` prowadzi do ekranu startowego.

## Etykiety (do zapisu w `projekt_strony.sqlite`, tabela `sekcja_ukladu`): `sekcja_ukladu_propozycja.tsv`

## Jak strona części zarządzania trafia do ramy bez drugiego hasła (`build_wersja_www_pelna.diff`)
Powłoka `/pelny/` dostaje funkcję `WWW_RAMA.strona(<strona>.html)`. Odszyfrowuje ona plik `pelny/aplikacja/<strona>.html.bin`
kluczem strony `/pelny/`, tak samo jak karty charakterystyki. Do ustalenia z częścią złożenia całości: kto zapisuje te pliki `.bin`
(proponuję krok 6 wydania, z tej samej treści co dziś `pelny/aplikacja/*.html`). Potrzebne też są wpisy na obu listach dozwolonych plików
(W-07 i `.github/skrypty/sprawdz_publikacje.py`). Część zarządzania BHP może dodać tryb „w ramie” (bez paska). Do tego czasu rama ukrywa pasek stylem.

## Sprawdzenie
`obchod2.js` przechodzi ekrany na 390×844 i 1366×768. Zrzuty z danymi osób są tylko we wspólnym folderze projektu, nie w tym repozytorium.

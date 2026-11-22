# Aplikacja CURL – strony www

Aplikacja CURL Centrum Uprawy Roślin Leczniczych IUNG-PIB w Sarnowie.
Strona: https://tomasz1961.github.io/kurs-bhp-curl/

Strona publiczna pokazuje tylko informację o aplikacji i dwa przyciski logowania. Treść szkoleń, testy, zarządzanie BHP
i karty charakterystyki są wyłącznie w zaszyfrowanych stronach /pelny/ i /pracownik/ (otwierają się hasłem strony).
Karty charakterystyki są zaszyfrowane (pliki <strona>/sds/*.bin) i otwierają się dopiero po zalogowaniu.

Publikacja: przepływ .github/workflows/strona.yml publikuje wszystkie pliki poza .git, .github, tests/ i README.md
i zatrzymuje publikację, jeśli znajdzie jawny plik PDF albo plik spoza listy dozwolonych. Wymaga ustawienia
Settings → Pages → Source: „GitHub Actions”.

## Wcześniejsza wersja

Zaszyfrowana strona wersji z 18.11.2026 pozostaje tylko pod adresem wersja-2026-11-18/pelny/. Wersję dla pracowników z 18.11.2026 usunięto 22.11.2026, bo zawierała dane osobowe wszystkich osób.
Jawna strona tej wersji i jawne karty charakterystyki zostały usunięte z publikacji (polecenie z 19.11.2026: karty
charakterystyki i treść tylko po zalogowaniu).

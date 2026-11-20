#!/usr/bin/env bash
# Sprawdzenie opublikowanej strony (uwagi przeglądu PR #32, polecenie TS z 20.11.2026):
#   strona główna i KAŻDA zaszyfrowana karta pelny/sds/*.bin = 200,
#   KAŻDA dawna jawna karta w obu miejscach (sds/<nazwa> i pelny/sds/<nazwa>) = 404,
#   pliki wewnętrzne (README, testy, archiwum, workflow) = 404.
# Użycie: sprawdz_strone_na_zywo.sh <adres strony> [katalog z pelny/sds/*.bin, domyślnie bieżący]
# Tryb --negatywny: ta sama kontrola na lokalnym serwerze z kopią strony, do której dopisano jawną kartę
# INNĄ NIŻ PIERWSZA (raz w sds/, raz w pelny/sds/) – kontrola musi dać błąd; inaczej kod 2.
set -euo pipefail
shopt -s nullglob

sprawdz_strone() {
  local U="${1%/}/" kat="${2:-.}" zle=0 plik B K p
  local karty=("$kat"/pelny/sds/*.bin)
  if [ "${#karty[@]}" -eq 0 ]; then echo "BŁĄD: brak zaszyfrowanych kart w $kat/pelny/sds/*.bin"; return 1; fi
  echo "Sprawdzenie strony $U (kart: ${#karty[@]})"
  kod() {
    local c
    c=$(curl -sS -g --retry 3 --retry-delay 2 --max-time 20 -o /dev/null -w '%{http_code}' "$U$(printf '%s' "$1" | sed 's/ /%20/g')") || c=000
    echo "$c $1 (oczekiwane $2)"
    [ "$c" = "$2" ] || zle=1
  }
  kod "" 200
  for plik in "${karty[@]}"; do
    B=$(basename "$plik"); K="${B%.bin}"
    kod "pelny/sds/$B" 200
    kod "sds/$K" 404
    kod "pelny/sds/$K" 404
  done
  for p in README.md tests/test_www.js wersja-2026-11-18/index.html .github/workflows/strona.yml; do kod "$p" 404; done
  if [ "$zle" -ne 0 ]; then
    echo "BŁĄD: na stronie są pliki, których nie powinno być, albo brakuje oczekiwanych (sprawdź też źródło Pages: GitHub Actions)"
    return 1
  fi
  echo "OK: strona bez jawnych kart i plików wewnętrznych"
}

test_negatywny() {
  local kat="${1:-.}" d port=8765 karty wynik=0
  karty=("$kat"/pelny/sds/*.bin)
  if [ "${#karty[@]}" -lt 2 ]; then echo "BŁĄD testu: potrzebne co najmniej 2 karty"; return 2; fi
  d=$(mktemp -d)
  tar -C "$kat" --exclude=./.git --exclude=./.github --exclude=./tests --exclude=./README.md --exclude=./_site -cf - . | tar -C "$d" -xf -
  ( cd "$d" && exec python3 -m http.server "$port" >/dev/null 2>&1 ) &
  local srv=$!
  sleep 2
  # kontrola wzorcowa: poprawna kopia strony przechodzi
  if ! sprawdz_strone "http://localhost:$port/" "$kat" >/dev/null; then echo "BŁĄD testu: poprawna kopia strony nie przeszła"; wynik=2; fi
  # karta druga i ostatnia (nie pierwsza) jako jawny plik w obu dawnych miejscach
  local B2 K2 BL KL
  B2=$(basename "${karty[1]}"); K2="${B2%.bin}"
  BL=$(basename "${karty[-1]}"); KL="${BL%.bin}"
  mkdir -p "$d/sds"; echo jawna > "$d/sds/$K2"
  if sprawdz_strone "http://localhost:$port/" "$kat" >/dev/null; then echo "BŁĄD testu: nie wykryto jawnej karty $K2 w sds/"; wynik=2; fi
  rm -f "$d/sds/$K2"; echo jawna > "$d/pelny/sds/$KL"
  if sprawdz_strone "http://localhost:$port/" "$kat" >/dev/null; then echo "BŁĄD testu: nie wykryto jawnej karty $KL w pelny/sds/"; wynik=2; fi
  kill "$srv" 2>/dev/null || true
  rm -rf "${d:?}"
  [ "$wynik" -eq 0 ] && echo "test negatywny strony na żywo: WYKRYTO jawną kartę inną niż pierwsza (sds/$K2, pelny/sds/$KL)"
  return "$wynik"
}

if [ "${1:-}" = "--negatywny" ]; then test_negatywny "${2:-.}"; else sprawdz_strone "${1:?adres strony}" "${2:-.}"; fi

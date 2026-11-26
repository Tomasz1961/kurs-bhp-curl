#!/bin/bash
# Jeden skrypt wydania aplikacji CURL (U31, A14-01; TS 18.11.2026 09:49 „scalamy”, 09:55 „chcę mieć to teraz”).
# Od wspólnego wydania 18.11 żadna część (kadry, szkolenia, zarządzanie BHP) nie wydaje stron sama.
# Kolejność (każdy krok ≠0 = STOP, dalsze kroki nie ruszają, wiersz APLIKACJA w wspolne/projekt/przebiegi_silnikow.tsv):
#  1 KADRY           – adm.sqlite w folderze = plik zatwierdzony przez kadry (wiersz ADM do_wydania_aplikacji ZGODNE z jego sha256)
#  2 SZKOLENIA       – łańcuch szkoleń lancuch_kursu.sh (z blokadą), kod 0
#  3 ZARZADZANIE_BHP – zestaw stron do_www = zestaw zatwierdzony (wiersz SYSTEM do_wydania_aplikacji ZGODNE z sha256 MANIFEST.json)
#  3b KOPIA WEJŚĆ   – kopia_wejsc.py: spójna kopia baz części i strony szkoleń; krok 5 składa jedną bazę z tej kopii, 6b sprawdza,
#                      że źródła po złożeniu stron mają treść równą kopii (inaczej STOP)
#  4 KONTROLA        – kontrola_projektu.py w trybie wydania aplikacji: K01–K18 STOP, w tym jedno menu (K17) i nazwa „aplikacja” (K18)
#  4b WYKRYWACZ    – bledy/wykrywacz.py: rejestr błędów, wykrywacze z testem negatywnym, naprawa aż do skutku
#  4c SILNIK KOSZTÓW – wspolne/koszty/sprawdz_silnik_kosztow.py: rozdział kosztów VS odtworzony z kopii kodu, 6 tabel = kopia koszty.sqlite
#  5 JEDNA BAZA      – zloz_baze.py: aplikacja_curl.sqlite, każda tabela z liczbą wierszy i sumą kontrolną = źródło
#  5c ODCISK        – odcisk_czesci.py: dane zarządzania BHP w jednej bazie = dane, z których zbudowano zatwierdzony zestaw
#  7 TEST WYDANYCH  – test_wydanych_stron.py (nazwa całości, pliki bez skryptu, odszyfrowanie), test części szkoleń na REPO_WWW
#                      i 7b: test_stron.py części zarządzania BHP z jej zapisu (zapis_systemu_pelny) na odszyfrowanych stronach
#  6 STRONY WWW      – budowa stron szkoleń wyłącznie z aplikacja_curl.sqlite (APLIKACJA_BAZA, ust_szkolen.polacz); jeden zestaw: wersja publiczna, /pelny/ (szkolenia), /pelny/aplikacja/ (zarządzanie BHP) do katalogu REPO_WWW
#  6p PRZYPOMNIENIA – adm/skrypty/build_przypomnienia_www.py do katalogu tymczasowego (PRZYPOMNIENIA_JAWNE); szyfrowanie i /przypomnienia/<obszar>/ w kroku 6 części szkoleń
#                      (klon kurs-bhp-curl); hasło tylko w zmiennej HASLO_WWW. Prośbę o scalenie otwiera uruchamiający, jedną.
# Zmienne: REPO_WWW, HASLO_WWW, HASLO_WWW_PRAC (hasło /pracownik/), PINY_WWW (skróty PIN-ów spoza repo) – wymagane w kroku 6 (/pelny/, /pracownik/ = TRYB_WWW=pracownik, /pelny/aplikacja/), BEZ_LANCUCHA=1 (pomija krok 2, gdy łańcuch przeszedł
# przed chwilą: wtedy wymagany wiersz KURS ZGODNE z sha256 bieżącego kurs_bhp_curl.html). Bez LLM.
set -u
PF=/mnt/project-files; W=$PF/wspolne; A=$W/aplikacja; B=$PF/bhp
TSV=${PRZEBIEGI_TSV:-$W/projekt/przebiegi_silnikow.tsv}
LOG=$A/wydanie_ostatnie.log
teraz() { date -u +%Y-%m-%dT%H:%M:%SZ; }
wiersz() { printf '%s\tAPLIKACJA\twydanie_aplikacji\t%s\t%s\t%s\n' "$(teraz)" "$1" "$2" "$3" >> "$TSV"; }
stop() { echo "STOP krok $1: $2" | tee -a "$LOG"; wiersz STOP "${SUMA:-}" "krok $1: $2"; exit 1; }
sha() { sha256sum "$1" | cut -c1-64; }
# ostatni wiersz silnika $1 i kroku $2 z wynikiem ZGODNE: zwraca kolumnę sha256_wejsc
zatwierdzony() { awk -F'\t' -v s="$1" -v k="$2" -f "$A/zatwierdzony.awk" "$TSV"; }

# zamek lokalny: flock na /mnt/project-files (rclone) nie szereguje – każde otwarcie to inny węzeł (wątek szkoleń 20.11 05:22)
exec 9>/tmp/aplikacja_wydanie.lock; flock -n 9 || { echo "STOP: inne wydanie w toku"; exit 1; }
# katalogi tymczasowe (kopia zestawu, kopia wejść, odszyfrowane strony, drzewo WORKSPACE) sprzątane zawsze, także po STOP
# (19.11.2026: trzy pozostawione kopie WORKSPACE, 14 GB, zapełniły dysk i zatrzymały krok 7b)
ZEST=; WEJ=; WYD=; DRZ=; PRZYP=
trap 'rm -rf "${ZEST:-/nonexistent}" "${WEJ:-/nonexistent}" "${WYD:-/nonexistent}" "${DRZ:-/nonexistent}" "${PRZYP:-/nonexistent}" "${WYD:-/nonexistent}.tresc"' EXIT
: > "$LOG"
echo "$(teraz) start wydania aplikacji" | tee -a "$LOG"
# 0 NARZĘDZIA: odczyt kart charakterystyki dwiema metodami wymaga OCR (łańcuch szkoleń: brak = STOP)
for n in tesseract pdftotext pdftoppm; do command -v $n >/dev/null || stop 0 "brak programu $n (apt-get install tesseract-ocr tesseract-ocr-pol poppler-utils)"; done

# 1 KADRY
python3 -I $A/test_zatwierdzony.py >> "$LOG" 2>&1 || stop 1 "test zatwierdzenia (wycofanie wierszem STOP) nie przeszedł"
bash $A/zatwierdzony_plik.sh $PF/adm/adm.sqlite ADM "$TSV" >> "$LOG" 2>&1 || stop 1 "adm.sqlite w folderze nie jest plikiem zatwierdzonym przez kadry"
echo "1 KADRY zgodne" | tee -a "$LOG"

# 2 SZKOLENIA
if [ "${BEZ_LANCUCHA:-}" = 1 ]; then
  ZK=$(awk -f "$A/strona_kursu_lancuch.awk" "$TSV")
  [ -n "$ZK" ] && [ "$(sha $B/kurs_online/kurs_bhp_curl.html)" = "$ZK" ] \
    || stop 2 "brak zgodnego przebiegu łańcucha szkoleń dla bieżącej strony szkoleń"
else
  # łańcuch sam bierze zamek lokalny /tmp/bhp_lancuch.lock (zamek na folderze sieciowym nic nie dawał)
  ( cd $B/skrypty && bash lancuch_kursu.sh > $B/raporty/przebieg_codzienny_ostatni.log 2>&1 ) \
    || stop 2 "łańcuch szkoleń: $(grep -m1 '^STOP' $B/raporty/przebieg_codzienny_ostatni.log | cut -c1-200)"
  printf '%s\tKURS\tlancuch_kursu\tZGODNE\t%s\tkurs %s (przebieg w wydaniu aplikacji)\n' "$(teraz)" "$(sha $B/kurs_online/kurs_bhp_curl.html)" "$(sha $B/kurs_online/kurs_bhp_curl.html | cut -c1-16)" >> "$TSV"
fi
echo "2 SZKOLENIA zgodne" | tee -a "$LOG"

# 3 ZARZADZANIE BHP
# kopia zestawu na czas wydania: podmiana do_www w trakcie nie zmienia tego, co sprawdzono i co trafia na www
ZEST=$(mktemp -d); cp -a $B/system/do_www/. "$ZEST/"
bash $A/zatwierdzony_plik.sh $ZEST/MANIFEST.json SYSTEM "$TSV" >> "$LOG" 2>&1 || stop 3 "zestaw stron zarządzania BHP nie jest zestawem zatwierdzonym"
echo "3 ZARZADZANIE_BHP zgodne" | tee -a "$LOG"

# 3b KOPIA WEJŚĆ (etap 5): spójna kopia wszystkich baz części i strony szkoleń po łańcuchu; jedna baza powstaje z tej kopii,
# a po złożeniu stron (6b) źródła muszą mieć treść równą kopii – strony powstały z tych samych danych co aplikacja_curl.sqlite
WEJ=$(mktemp -d)
python3 -I $A/kopia_wejsc.py "$WEJ" >> "$LOG" 2>&1 || stop 3 "kopia wejść: $(grep -m1 '^STOP' "$LOG")"
baza_kopii() { awk -F'\t' -v c="$1" '$1==c{print $3}' "$WEJ/WEJSCIA.tsv"; }
echo "3b KOPIA WEJŚĆ zgodna" | tee -a "$LOG"

# 4 KONTROLA CAŁOŚCI
( cd $W/projekt && PROJEKT_SYSTEM_STRONY="$ZEST" PROJEKT_WYDANIE_APLIKACJI=1 python3 kontrola_projektu.py --bez-zapisu >> "$LOG" 2>&1 ) || stop 4 "kontrola całości: $(grep -m3 ' STOP ' "$LOG" | tr '\n' ' ' | cut -c1-300)"
echo "4 KONTROLA zgodna" | tee -a "$LOG"
# 4b WYKRYWACZ BŁĘDÓW (TS 19.11 04:52–04:56): każdy błąd z rejestru ma wykrywacz z testem negatywnym; cykl wykrycie → badanie → naprawa
python3 -I $A/bledy/wykrywacz.py >> "$LOG" 2>&1 || stop 4 "wykrywacz błędów: $(grep -m3 '^STOP' "$LOG" | tail -3 | tr '\n' ' ' | cut -c1-250)"
echo "4b WYKRYWACZ BŁĘDÓW zgodny" | tee -a "$LOG"

# 4c SILNIK KOSZTÓW (TS 24.11.2026 19:00 „ten mechanizm należy zachować”): rozdział kosztów odtworzony z kopii kodu VS = kopia koszty.sqlite
python3 -I $W/koszty/sprawdz_silnik_kosztow.py >> "$LOG" 2>&1 || stop 4 "silnik kosztów: $(tail -1 "$LOG" | cut -c1-200)"
echo "4c SILNIK KOSZTÓW zgodny" | tee -a "$LOG"

# 5 JEDNA BAZA
APLIKACJA_BAZA_KADRY=$(baza_kopii KADRY) APLIKACJA_BAZA_TERMINY=$(baza_kopii TERMINY) APLIKACJA_BAZA_SZKOLENIA=$(baza_kopii SZKOLENIA) \
APLIKACJA_BAZA_ZARZADZANIE_BHP=$(baza_kopii ZARZADZANIE_BHP) APLIKACJA_BAZA_POCZTA_BHP=$(baza_kopii POCZTA_BHP) APLIKACJA_BAZA_PROJEKT=$(baza_kopii PROJEKT) \
APLIKACJA_BAZA_KOSZTY=$(baza_kopii KOSZTY) APLIKACJA_BAZA_ANALIZY_UPRAWY=$(baza_kopii ANALIZY_UPRAWY) APLIKACJA_BAZA_ZAMOWIENIA=$(baza_kopii ZAMOWIENIA) \
  python3 -I $A/zloz_baze.py >> "$LOG" 2>&1 || stop 5 "jedna baza: kopia niezgodna ze źródłem"
SUMA=$(sha $A/aplikacja_curl.sqlite)
echo "5 JEDNA BAZA zgodna $SUMA" | tee -a "$LOG"
# 5c odcisk części zarządzania BHP w jednej bazie = odcisk w zatwierdzonym zestawie (do_www liczy go z bazy złożonej z ich bazy)
python3 -I $A/odcisk_czesci.py $A/aplikacja_curl.sqlite ZARZADZANIE_BHP "$ZEST/MANIFEST.json" >> "$LOG" 2>&1 \
  || stop 5 "$(tail -1 "$LOG" | cut -c1-200)"
echo "5c ODCISK ZARZĄDZANIA BHP zgodny" | tee -a "$LOG"

# 6 STRONY WWW
if [ -z "${REPO_WWW:-}" ] || [ -z "${HASLO_WWW:-}" ] || [ -z "${PINY_WWW:-}" ]; then
  wiersz ZGODNE_BEZ_WWW "$SUMA" "kroki 1–5 zgodne; strony nie złożone (brak REPO_WWW/HASLO_WWW/PINY_WWW)"
  bash $A/kopia_zapasowa.sh "wydanie bez stron www $SUMA" | tee -a "$LOG" || stop 8 "kopia zapasowa nieudana"
  echo "ZGODNE bez stron www"; exit 0
fi
# 6p PRZYPOMNIENIA (TS 24.11.2026 15:37/15:50): panel dokumentów do dołączenia, obszar → miejsce → aspekt, 8 stron S_…;
#    treść jawna tylko w katalogu tymczasowym poza REPO_WWW (PRZYPOMNIENIA_JAWNE), szyfruje i publikuje część szkoleń w /przypomnienia/<obszar>/
PRZYP=$(mktemp -d)
APLIKACJA_BAZA=$A/aplikacja_curl.sqlite python3 -I $PF/adm/skrypty/build_przypomnienia_www.py "$PRZYP" >> "$LOG" 2>&1 \
  || stop 6 "przypomnienia: $(grep -m1 'PW-01' "$LOG" | cut -c1-200)"
[ "$(find "$PRZYP" -mindepth 2 -maxdepth 2 -name index.html | wc -l)" -ge 1 ] || stop 6 "przypomnienia: brak stron obszarów w katalogu roboczym"
case "$PRZYP" in "$REPO_WWW"*) stop 6 "przypomnienia: katalog jawny wewnątrz REPO_WWW";; esac
export PRZYPOMNIENIA_JAWNE="$PRZYP"
( cd $B/skrypty && export APLIKACJA_BAZA=$A/aplikacja_curl.sqlite && python3 build_wersja_www.py && cp "$B/www/index.html" "$REPO_WWW/index.html" && python3 build_wersja_www_pelna.py "$REPO_WWW" && TRYB_WWW=pracownik HASLO_WWW="${HASLO_WWW_PRAC:?brak HASLO_WWW_PRAC}" python3 build_wersja_www_pelna.py "$REPO_WWW" && APLIKACJA_WWW_ZRODLO="$ZEST" python3 build_aplikacja_www.py "$REPO_WWW" ) >> "$LOG" 2>&1 \
  || stop 6 "składanie stron www"
python3 -I $A/kopia_wejsc.py "$WEJ" --sprawdz >> "$LOG" 2>&1 || stop 6 "dane części zmieniły się w trakcie składania stron: $(grep -m2 '^STOP' "$LOG" | tail -1 | cut -c1-200)"
echo "6 STRONY WWW złożone z danych równych jednej bazie" | tee -a "$LOG"

# 7 TEST WYDANYCH STRON (TS 18.11 17:42–17:46): sprawdzany jest wynik w REPO_WWW, nie źródło
python3 -I $A/test_negatywny_wydanych_stron.py >> "$LOG" 2>&1 || stop 7 "test kroku 7 nie wykrywa uszkodzeń (test negatywny)"
WYD=$(mktemp -d)
python3 -I $A/test_wydanych_stron.py "$REPO_WWW" --raport $A/przeglad/krok7_ostatni.tsv --wypakuj "$WYD" --wypakuj-tresc "$WYD.tresc" >> "$LOG" 2>&1 \
  || stop 7 "wydane strony: $(grep -m1 '^WYNIK' $A/przeglad/krok7_ostatni.tsv 2>/dev/null; tail -n +2 $A/przeglad/krok7_ostatni.tsv | head -3 | tr '\t\n' '  ' | cut -c1-250)"
[ -f $B/skrypty/kontrola/test_strony_www_wydanie.py ] || stop 7 "brak testu wydanych stron części szkoleń (kontrola/test_strony_www_wydanie.py)"
( cd $B/skrypty && python3 kontrola/test_strony_www_wydanie.py "$REPO_WWW" ) >> "$LOG" 2>&1 || stop 7 "wydane strony części szkoleń niezgodne z bazą (PIN-y, hasła, role, zapis)"
# 7b test części zarządzania BHP na wydanych stronach: jej test_stron.py z zapisu, z którego powstał zatwierdzony zestaw
ZAPIS=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('zapis_systemu_pelny',''))" "$ZEST/MANIFEST.json")
[ ${#ZAPIS} = 40 ] || stop 7 "zestaw zarządzania BHP bez pełnego zapisu źródłowego (zapis_systemu_pelny)"
DRZ=$(mktemp -d)
( cd "$DRZ" && git init -q && git remote add origin https://github.com/Tomasz1961/WORKSPACE.git && git fetch -q --depth 1 origin "$ZAPIS" && git checkout -q FETCH_HEAD ) >> "$LOG" 2>&1 \
  || stop 7 "nie da się pobrać zapisu $ZAPIS części zarządzania BHP"
( cd "$DRZ/administracja-iung/system-bhp" && python3 skrypty/test_stron.py --baza-aplikacji $A/aplikacja_curl.sqlite --zestaw "$WYD" ) >> "$LOG" 2>&1 \
  || stop 7 "wydane strony zarządzania BHP niezgodne z jedną bazą (test_stron.py --zestaw)"
# 7c WYGLĄD (TS 19.11 18:20): zasady tylko z wspolne/projekt/strona/projekt_strony.sqlite; kontrola bazy, potem pomiar wyrenderowanej
#    odszyfrowanej treści stron szkoleń w ustawieniu jasnym i ciemnym (kontrast_ekranu.js --zapis dopisuje wynik do bazy)
S=$PF/wspolne/projekt/strona
python3 $S/projekt_strony.py --kontrola >> "$LOG" 2>&1 || stop 7 "kontrola bazy projektu strony (projekt_strony.py --kontrola)"
ls "$WYD.tresc"/*.html >/dev/null 2>&1 || stop 7 "brak odszyfrowanej treści stron szkoleń do pomiaru ekranu"
for T in "$WYD.tresc"/*.html; do
  ZRZUTY=$(mktemp -d) node --no-warnings $S/kontrast_ekranu.js "$T" '#rama_alarm_przycisk' --zapis >> "$LOG" 2>&1 \
    || stop 7 "wygląd $(basename "$T"): $(grep '^WYNIK' "$LOG" | tail -1) – szczegóły: projekt_strony.sqlite pomiar_ekranu"
done
echo "7 TEST WYDANYCH STRON zgodny" | tee -a "$LOG"
wiersz ZGODNE "$SUMA" "kroki 1–7 zgodne; strony w $REPO_WWW, kurs $(sha $B/kurs_online/kurs_bhp_curl.html | cut -c1-16), zarządzanie $(sha $ZEST/MANIFEST.json | cut -c1-16)"
bash $A/kopia_zapasowa.sh "wydanie $SUMA" | tee -a "$LOG" || stop 8 "kopia zapasowa nieudana"
echo "ZGODNE: aplikacja złożona; otwórz jedną prośbę o scalenie z $REPO_WWW" | tee -a "$LOG"

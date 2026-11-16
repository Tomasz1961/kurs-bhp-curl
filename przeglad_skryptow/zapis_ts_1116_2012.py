#!/usr/bin/env python3
"""Zapis słów TS 16.11.2026 20:12:51 UTC (czat projektu, przekazane do wątku kursu) w decyzja_ts PRZED pracą (zasada R-12, TS 17:06
„Mówiłem o tym, ale tego nie odnotowałeś”). Cytat dosłownie z pliku zrodla/ts_2026-11-16_2012_uwagi_kurs.txt (sha w kolumnie zrodlo).
Reguły z wypowiedzi rozpisane w decyzja_ts 146–151 (jedna reguła = jeden wiersz = kontrola D-146..D-151). Idempotentne, bez LLM."""
import os, sqlite3, hashlib
B = '/mnt/project-files/bhp'
P = f'{B}/zrodla/ts_2026-11-16_2012_uwagi_kurs.txt'
cyt = open(P, encoding='utf-8').read().strip()
sha = hashlib.sha256(cyt.encode()).hexdigest()[:16]
ZR = f'czat projektu, TS 16.11.2026 20:12:51 UTC (cmsg_01LjRRUGCMRdzeCLcFKfUaaMQnsCcUcvofpxWn2UuAHP2V); pełny cytat: zrodla/ts_2026-11-16_2012_uwagi_kurs.txt sha256 {sha}'
def frag(a, b):
    i = cyt.index(a); j = cyt.index(b, i) + len(b); return cyt[i:j]
R = [
 (146, frag('Co za pierdolenie', 'nowoczesne ujęcie, jakoś kurwa zrozum.'),
  'Opis planu obiektu mówi, czemu służy plan: część uprawowa (7 boksów, mnożarka, klonownik), część pozbiorowa (pomieszczenia czyste za śluzami: trymowanie, suszenie, pakowanie, magazynowanie), magazyny, część biurowa i socjalna; GACP (EMA), monitoring i ochrona, ustawa o przeciwdziałaniu narkomanii, zezwolenie GIF; droga jednokierunkowa; do miejsc przypisane ryzyka, instrukcje, SOP, karty charakterystyki, sprzęt, ostrzeżenia; plan jako warstwa dokumentacji, szkoleń, utrzymania, kalibracji i identyfikowalności. Bez szczegółów wewnętrznych (np. „boks zmniejszony”, „zatwierdzony przez …”). Akty i artykuły tylko z rejestru aktów, nie z pamięci.',
  'opis planu: fragment systemu BHP (właściciel – wątek systemu BHP, przekazane 16.11 20:2x); kurs: kontrola D-146 słów zakazanych na zakładkach Obiekt'),
 (147, frag('Zakazałem używania', 'Wszystko pod tym kątem.'),
  'Kurs uczy wg pytań uczestnika: gdzie jestem, co robię, co mi grozi, skąd się dowiem, jak postępować, jak udokumentować, co dzieje się w kolejnym miejscu, jak krok po kroku idą rośliny i proces. Bez wewnętrznych określeń technicznych.',
  'krok 11zz9; kontrola D-147'),
 (148, frag('Po prostu jak się otworzy', 'małymi kawałkami.'),
  'Po otwarciu najpierw treść: czym jest centrum, jakie są szkolenia i kto musi co odbyć; nazwiska i lista osób dopiero dalej, nie na stronie startowej. Moduły krok po kroku, małymi kawałkami.',
  'krok 11zz9; kontrola D-148 (pierwszy widok bez nazwisk)'),
 (149, frag('Naucz się mówić', 'obrazowo.'),
  'Język: polski, zrozumiały, niekolokwialny, prosty, techniczny, profesjonalny, przekonujący, obrazowy; bez skrótów wewnętrznych.',
  'kontrola_jezyk (słowa wewnętrzne) + przegląd zakładek; kontrola D-149'),
 (150, frag('I każdy obrazek', 'rozwijać już dalej.'),
  'Każdy obrazek w kursie ma objaśnienie, co pokazuje i dlaczego to dobrze albo źle; obrazki wchodzą do pytań „dobrze czy źle i dlaczego”.',
  'krok 11zz9 (objaśnienia) i 11zz10 (pytania obrazkowe); kontrola D-150'),
 (151, frag('Dlatego w każdym tym silniku', 'nauczyć uczyć.'),
  'Te same nazwy SOP, zapisów i przepisów we wszystkich silnikach; rozbieżności uzgadniane w cyklach (najpóźniejsze, spójne, najczęstsze, potwierdzone), zapisane w skrypcie.',
  'wspólnie z wątkiem systemu BHP (sorter rozbieżności); kontrola D-151'),
]
c = sqlite3.connect(os.environ.get('BHP_DB', f'{B}/bhp_rejestr.sqlite'))
for i, cy, d, w in R:
    c.execute('insert or ignore into decyzja_ts(id, czas_utc, cytat, decyzja, wdrozenie, status, zrodlo) values(?,?,?,?,?,?,?)',
              (i, '2026-11-16T20:12:51Z', cy, d, w, 'W TOKU', ZR))
c.commit()
print('decyzje 146–151 zapisane:', c.execute('select count(*) from decyzja_ts where id between 146 and 151').fetchone()[0], '| sha cytatu', sha)
# TS 16.11.2026 20:16:19 UTC: nie przebudowywać od nowa; jeden projekt aplikacji jako wzorzec z kontrolą (dec. 152)
P2 = f'{B}/zrodla/ts_2026-11-16_2016_projekt_aplikacji.txt'
t2 = open(P2, encoding='utf-8').read().strip()
c.execute('insert or ignore into decyzja_ts(id, czas_utc, cytat, decyzja, wdrozenie, status, zrodlo) values(152,?,?,?,?,?,?)', ('2026-11-16T20:16:19Z', t2,
 'Nie przebudowywać kursu od nowa: usprawniać istniejący w stronę decyzji 146–151. Jeden projekt aplikacji (moduły, jak się zazębiają, relacje bazy, skrypty) zapisany w SQLite jako obowiązujący wzorzec; każda zmiana kursu i systemu sprawdzana z nim (kontrola).',
 'projekt aplikacji: uzgodnienie z wątkiem systemu BHP (plan jednej aplikacji 16.11); kontrola D-152', 'W TOKU',
 'czat projektu, TS 16.11.2026 20:16:19 UTC (cmsg_01LjRRUGCMRdzeCLcFKfUaaMJGN8ZmbgQMMZAu5tq2veht); zrodla/ts_2026-11-16_2016_projekt_aplikacji.txt sha256 ' + hashlib.sha256(t2.encode()).hexdigest()[:16]))
c.commit()
# TS 16.11.2026 21:04:20 UTC: role i adresy do wiadomości przypisywane w panelu Administratora (dec. 154; usprawnienie U19 projektu aplikacji)
t3 = open(f'{B}/zrodla/ts_2026-11-16_2104_role_maile.txt', encoding='utf-8').read().strip()
c.execute('insert or ignore into decyzja_ts(id, czas_utc, cytat, decyzja, wdrozenie, status, zrodlo) values(154,?,?,?,?,?,?)', ('2026-11-16T21:04:20Z', t3,
 'W panelu Administratora zakładka „Role i uprawnienia”: Administrator przypisuje osobę i e-mail do roli (kadry, zaopatrzenie, dział BHP, QA); z roli wynika, kto wgrywa jakie dokumenty i kto dostaje wiadomości o brakach; zmiana z zapisem kto i kiedy. Adresy i zgody wysyłki zostają w ADM.',
 'usprawnienie U19 (kolejka kursu po U01); tabela przypisań do uzgodnienia z wątkiem ADM', 'W TOKU',
 'czat projektu, TS 16.11.2026 21:04:20 UTC (cmsg_01LjRRUGCMRdzeCLcFKfUaaMVRBVX1FTwgYZQPYPowysxM); zrodla/ts_2026-11-16_2104_role_maile.txt'))
c.commit()

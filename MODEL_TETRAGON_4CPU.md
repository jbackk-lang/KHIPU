# MODEL_TETRAGON_4CPU — architektura czteroprocesorowa

> **[TU JEST WERSJA 4-PROCESOROWA]** To jest rozszerzenie do 4 CPU,
> którego nie ma (i nigdy nie było) w
> [jbackk-lang/PC_TIMDR](https://github.com/jbackk-lang/PC_TIMDR) -
> jeśli szukasz modelu wieloprocesorowego wspomnianego przy okazji
> PC_TIMDR, to jest właśnie ten plik (`khipu/tetragon.py`,
> `khipu/axis.py`, `khipu/rope48.py`, realnie zaimplementowane i
> przetestowane).


Scalony dokument. Zastępuje: `MODEL_TETRAGON_4CPU.md` (starą wersję) +
`RESONANCE_COMM.md` + architektoniczną część dawnego `README.md` — te
trzy pliki opisywały tę samą architekturę niemal dosłownie się powielając
(README był w praktyce sklejeniem pozostałych dwóch). Mapowanie w
`REORGANIZACJA.md`.

Pełny model czteroprocesorowej architektury topologicznej opartej na
skręcie, kierunku, sznurach izometrycznych ROPE48 oraz komunikacji
rezonansowej przez figurę tetragonalną. Cztery identyczne procesory
topologiczne współpracują poprzez wspólną figurę skrętu — bez magistrali,
ramek, adresów ani protokołów; komunikacja odbywa się przez **rezonans
geometryczny** (propagacja zmiany skrętu przez wspólny węzeł osiowy).

---

## 1. Procesory topologiczne (CPU_A, CPU_B, CPU_C, CPU_D)

Cztery identyczne CPU_CORE_16 (patrz `MODEL_PC.md` §1). Każdy generuje
własne S, K, idx i aktualizuje własny sznur ROPE48_X.

## 2. Sznury ROPE48 (4 × 12 na CPU)

- 4 warstwy × 12 pozycji = 48 węzłów na sznur
- izometria: długość sznura zawsze = 48, brzeg domknięty (cykl)
- każdy węzeł: S, K, D, B, W, L, R (jak NODE256, patrz `MODEL_PC.md` §2)

## 3. Węzeł osiowy (NODE_AXIS)

Wspólny punkt skrętu dla wszystkich CPU: `S_axis, K_axis, B_axis, L_axis, R_axis`.

Połączenia: `ROPE48_A/B/C/D ↔ NODE_AXIS`. Zasada: połączenia między
sznurami idą wyłącznie przez NODE_AXIS — nie ma bezpośrednich,
przypadkowych połączeń A↔B↔C↔D.

## 4. LUT256 i VALIDATION_LAYER — wspólne

Jedna LUT256, jeden TIMDR i jeden GIPU dla wszystkich czterech CPU
(definicje jak w `MODEL_PC.md` §3 i §5, tu działają globalnie na
wszystkich CPU naraz).

## 5. Figury rezonansowe

**NAPRAWIONA NIESPÓJNOŚĆ (2026-08):** ta sekcja opisywała dawniej relacje
osiowe jako `R_AB_axis, R_BC_axis, ...` — czyli po jednej na KAŻDĄ krawędź
i przekątną figury (graf pełny, K3 dla trójkąta / K4 dla tetragonu). Kod
(`ResonanceFigure.axial_relations()`) rzeczywiście tak liczył, ALE
parametr `axis` (stan węzła osiowego) był przy tym całkowicie ignorowany
— czyli to była relacja bezpośrednia CPU↔CPU, nie relacja "przez oś", jak
głosi §3 wyżej ("połączenia idą WYŁĄCZNIE przez NODE_AXIS"). Naprawiono
kod, by faktycznie liczył relację względem osi — patrz niżej.

**TRÓJKĄT** (CPU A, B, C): relacje `R_A_axis, R_B_axis, R_C_axis` — jedna
na CPU, licząca relację GIPU między węzłem tego CPU a syntetycznym węzłem
osiowym (`s_axis`/`k_axis`). Efekt: 3 połączenia przez wspólną oś
(hub-and-spoke), propagacja ΔS przez węzeł osiowy.

**TETRAGON** (CPU A, B, C, D): relacje `R_A_axis, R_B_axis, R_C_axis,
R_D_axis` — jedna na CPU (4, nie 6), tym samym mechanizmem. Efekt: 4
połączenia przez wspólną oś, propagacja ΔS przez całą figurę bez
bezpośrednich połączeń A↔B↔C↔D.

Dawne, bezpośrednie relacje CPU↔CPU (graf pełny, z pominięciem osi) są
nadal dostępne jawnie przez `ResonanceFigure.direct_relations()` —
`R_AB, R_BC, R_CA` (trójkąt) / `R_AB, R_BC, R_CD, R_DA, R_AC, R_BD`
(tetragon) — jako narzędzie diagnostyczne do porównania z topologią
gwiazdy, NIE jako opis rzeczywistej architektury komunikacji.

## 6. Mechanizm komunikacji rezonansowej

1. CPU_X generuje S_X, K_X — TIMDR waliduje.
2. Zmiana ΔS_X trafia do NODE_AXIS.
3. NODE_AXIS propaguje ΔS do sąsiadów (boki figury), przekątnych
   (tylko tetragon) i warstw osiowych.
4. GIPU aktualizuje ROPE48_X lokalnie oraz relacje osiowe i figury
   rezonansowe globalnie.

## 7. Pojemność operacyjna

| | wzór | wynik |
|---|---|---|
| jeden CPU | 32 wejścia × 48 pozycji | **1536** stanów |
| tetragon (4 CPU) | 4 × 1536 | **6144** stanów |
| + rezonans trójkąta | 6144 × (1.15–1.20) | ~7065–7373 |
| + rezonans tetragonu | 6144 × (1.30–1.40) | ~7987–8602 (**~8000**) |

## 8. Właściwości architektury

- brak sygnałów, ramek, adresów, protokołów,
- komunikacja przez skręt, propagacja przez figurę,
- izometria i brzeg zachowane w każdym ROPE48,
- deterministyczne relacje,
- pojemność rośnie topologicznie (przez figury/relacje), nie bitowo.

## 9. Zastosowania (deklarowane)

AI topologiczne, modele rezonansowe, przetwarzanie równoległe bez
magistrali, systemy wieloprocesorowe bez konfliktów, architektury
geometryczne, modele predykcyjne oparte na skręcie, filtrowanie danych
z kamer ToF/LiDAR, analiza sygnałów w robotyce. **Uwaga:** to są
deklarowane kierunki zastosowań, nie zweryfikowane wyniki — architektura
nie była testowana na żadnym z tych realnych zastosowań.

---

## 10. Status implementacji

Zaimplementowane w `khipu/tetragon.py` (`TetragonSystem`) i
`khipu/axis.py` (`NodeAxis`, `ResonanceFigure`):

| Element specyfikacji | Moduł |
|---|---|
| CPU_A..D | `khipu.cpu.CPUCore16` × 4 |
| ROPE48_A..D | `khipu/rope48.py` |
| LUT256 / TIMDR / GIPU wspólne | reużyte z `MODEL_PC.md` |
| NODE_AXIS | `khipu/axis.py: NodeAxis` |
| Figury TRÓJKĄT/TETRAGON | `khipu/axis.py: ResonanceFigure` |
| Pojemność operacyjna | `TetragonSystem.capacity_*()` — zweryfikowana testem, zgadza się z liczbami z §7 |

### Naprawiony błąd: trwała awaria po 48 słowach na rdzeń (2026-08)

`Rope48.push()` rzucał dawniej `OverflowError` po dokładnie 48 wywołaniach
i BLOKOWAŁ dalsze działanie CPU na stałe (każdy kolejny `feed()` w
`TetragonSystem` kończył się nieobsłużonym wyjątkiem) — mimo że własny
docstring modułu od początku obiecywał "sznur CYKLICZNY". Realnie
oznaczało to twardy limit 192 słów (4 rdzenie × 48) na cały czas życia
systemu. **Naprawione**: `push()` jest teraz prawdziwym pierścieniem
FIFO — po zapełnieniu nadpisuje najstarszy wpis. Zmierzone: 200 000
słów przetworzone bez awarii, ~14 300 słów/s, każdy sznur trwale
utrzymuje dokładnie 48 najnowszych węzłów. Długość 48 (4×12, znaczenie
geometryczne wg architektury) NIE została podniesiona — to nie był
"za mały limit", tylko brakujące zawijanie.

### Naprawiona niespójność: axial_relations() ignorowało oś (2026-08)

Patrz §5 wyżej. `ResonanceFigure.axial_relations()` liczyło relacje
bezpośrednio CPU↔CPU (graf pełny K3/K4, 6 relacji dla tetragonu),
ignorując parametr `axis` — sprzeczne z własną dokumentacją modułu
("połączenia idą WYŁĄCZNIE przez oś"). Żaden z 62 testów tego nie
wyłapał (`test_axial_relations_covers_all_edges_and_diagonals` sprawdzało
tylko `len(rel) == 6`). Naprawione: relacja liczona jest teraz przez
syntetyczny węzeł osiowy (`axis.s_axis`/`axis.k_axis`), jedna na CPU
(`R_A_axis`..`R_D_axis`, 4 nie 6). Dawne zachowanie zachowane jawnie jako
`ResonanceFigure.direct_relations()`. Regresja:
`tests/test_axis.py::test_axial_relations_actually_depend_on_axis_state`.

### Uogólnienie na dowolne N CPU + wtyczkowy DETECT_SCREW (2026-08)

`ResonanceFigure` (patrz §5 wyżej) przyjmuje teraz, obok dawnych
`kind="triangle"`/`"tetragon"`, także `cpu_names=(...)` (jawne etykiety)
albo `n_cpus=N` (etykiety A,B,C.. generowane automatycznie). Krawędzie/
przekątne liczone są ogólnym wzorem wieloboku (boki = kolejne pary w
cyklu, przekątne = wszystkie pozostałe pary) — dla N=3/4 daje DOKŁADNIE
te same listy co dawne hardkodowane stałe (sprawdzone testem równości),
więc `kind="triangle"`/`"tetragon"` zachowuje się identycznie jak przed
uogólnieniem. `axial_relations()` (relacja przez oś, jedna na CPU)
działała już dla dowolnego N od razu, bo iteruje po `self.cpus`, nie po
krawędziach — to `direct_relations()` (graf pełny, diagnostyczne) i
`resonance_boost()` wymagały uogólnienia; `resonance_boost()` pozostaje
zdefiniowane TYLKO dla 3/4 CPU (klucz po LICZBIE CPU, nie po `kind`, żeby
działało też dla własnych etykiet) i rzuca `NotImplementedError` dla
innego N zamiast zgadywać liczbę bez podstawy źródłowej.

Przy tej okazji naprawiony utajony błąd w `TetragonSystem`: figura
zawsze budowała się z hardkodowanych etykiet `("A","B","C","D")`/
`("A","B","C")`, niezależnie od TREŚCI faktycznych `cpu_names` przekazanych
do konstruktora — dla domyślnych etykiet niezauważalne (bo identyczne),
ale dla własnych nazw (`cpu_names=("W","X","Y","Z")`) klucze figury i
`nodes_by_cpu` byłyby różne, a `axial_relations()`/`direct_relations()`
cicho zwracałyby puste/błędne wyniki. Naprawione: figura dostaje zawsze
`cpu_names=self.cpu_names` wprost.

Dodatkowo `TetragonSystem(classifier_fn=...)` (jak `CPUCore16`, patrz
`MODEL_PC.md`) — przekazywane do KAŻDEGO CPU w tetragonie (wszystkie są
"identyczne" wg dokumentacji, więc dostają ten sam wstrzyknięty
klasyfikator).

Regresje: `tests/test_axis.py` (5 nowych testów N-CPU),
`tests/test_tetragon.py::test_custom_cpu_names_figure_uses_matching_labels`,
`::test_five_cpu_tetragon_system_works_end_to_end`,
`::test_classifier_fn_propagates_to_all_cpus`.

### Eksperyment: realne zrównoleglenie 4 "CPU" (2026-08)

`TetragonSystem.feed()` przetwarza słowa sekwencyjnie w jednym wątku
Pythona (round-robin między CPU A/B/C/D) - żadnej prawdziwej
równoległości nie ma, mimo nazwy "4-procesorowy". Sprawdzone
eksperymentalnie w `benchmarks/parallel_vs_sequential.py`, czy realne
zrównoleglenie przez `multiprocessing` (prawdziwe procesy systemowe -
wątki nic by nie dały, GIL serializuje pracę CPU-bound) coś by dało.

**Ważne zastrzeżenie**: zmierzone na sandboxie z `os.cpu_count() == 2`,
NIE na docelowym sprzęcie użytkownika (4+ rdzeniowy Ryzen) - uruchom
skrypt lokalnie, żeby dostać liczby dla własnej maszyny.

Wyniki (200 000 słów):

| Tryb | słów/s | przyspieszenie | vs fizyczny sufit |
|---|---|---|---|
| 4 strumienie sekwencyjnie (1 proces) | 27 432 | - | - |
| 4 strumienie równolegle (`Pool(4)`, oversubskrybcja na 2 rdzeniach) | 36 513 | 1.33x | ~66% z 2.00x |
| 2 strumienie sekwencyjnie (1 proces) | 26 190 | - | - |
| 2 strumienie równolegle (`Pool(2)`, dopasowane do sprzętu) | 36 413 | 1.39x | ~70% z 2.00x |

Wnioski: równoległość realnie pomaga, ale skromnie, nie liniowo z liczbą
"CPU" - ograniczenia to (a) sandbox ma fizycznie tylko 2 rdzenie, nie 4,
(b) narzut multiprocessingu (spawn procesu, pickle danych) zjada część
zysku przy tak lekkiej pracy na pojedyncze słowo. Na prawdziwym 4+
rdzeniowym Ryzenie należy się spodziewać większego przyspieszenia niż
tutaj, ale prawdopodobnie wciąż poniżej pełnych 4.00x - efektywność
65-70% zmierzona tu na 2 rdzeniach jest typowa dla multiprocessingu przy
lekkich zadaniach. Sanity check: wyniki (nie tylko czas) identyczne w
obu trybach - `tests/test_benchmarks.py`.

Decyzje interpretacyjne specyficzne dla tego modułu (poza tymi
opisanymi w `MODEL_PC.md` §10):

- **Agregacja NODE_AXIS z 3–4 węzłów CPU** — nie podano wzoru; przyjęto
  głosowanie większościowe (moda) na każdej osi osobno (`axis.py`).
- **Zakres wzrostu pojemności dla figur** — dokumentacja podaje widełki
  (trójkąt +15–20%, tetragon +30–40%) bez jednej liczby; kod zwraca
  `(min, max, środek)` zamiast jednej wartości, żeby nie zgadywać na siłę.

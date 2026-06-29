# MODEL_TETRAGON_4CPU
Architektura czterech procesorów topologicznych połączonych izometrycznie (kwadratura + trójkąt/tetragon).

---

## CPU_TOPO_CORE (x4)
Cztery identyczne procesory topologiczne:

- CPU_A
- CPU_B
- CPU_C
- CPU_D

Każdy CPU:
- 16-bitowy rdzeń skrętu/kierunku
- DETECT_SCREW(word16) -> S
- DERIVE_DIRECTION(S) -> K
- EMIT_INDEX(S,K) -> idx

CPU nie liczy wyników, tylko:
- skręt (S)
- kierunek (K)
- indeks (idx)

---

## ROPE48 (4 × 12) PER CPU
Każdy procesor ma własny sznur:

- ROPE48_A
- ROPE48_B
- ROPE48_C
- ROPE48_D

Struktura ROPE48:
- 4 warstwy × 12 pozycji = 48 węzłów
- każdy węzeł = NODE:
  - S (skręt)
  - K (kierunek)
  - D (droga)
  - B (brzeg)
  - W (szerokość)
  - L (warstwa)
  - R (relacje)

Warunek:
- długość sznura = 48
- izometria warunku brzegowego zachowana
- każdy sznur jest cyklem domkniętym

---

## LUT256 (wspólna)
Jedna wspólna tablica LUT256 dla wszystkich CPU:

- wejście: idx = (S,K)
- wyjście: NODE (stan topologiczny)
- modyfikowalna przez TIMDR/GIPU

Każdy CPU:
- korzysta z tej samej LUT256
- różni się tylko sznurem (ROPE48_X)

---

## TIMDR / GIPU (globalne)
TIMDR:
- walidacja skrętu/kierunku dla wszystkich CPU
- pilnowanie osi 1/2 i φ
- może wymusić korektę S/K globalnie

GIPU:
- zarządza wszystkimi sznurami:
  - ROPE48_A/B/C/D
- pilnuje:
  - relacji wewnątrz sznura
  - relacji między sznurami
  - rezonansów trójkątnych/tetragonalnych

---

## AXIS_NODE (węzeł osiowy)
Wspólny węzeł centralny, łączący 4 sznury:

- NODE_AXIS:
  - S_axis (skręt osiowy)
  - K_axis (kierunek osiowy)
  - B_axis (brzeg nadrzędny)
  - L_axis (warstwa osiowa)
  - R_axis (relacje osiowe)

Połączenia:
- ROPE48_A ↔ NODE_AXIS
- ROPE48_B ↔ NODE_AXIS
- ROPE48_C ↔ NODE_AXIS
- ROPE48_D ↔ NODE_AXIS

Zasada:
- połączenia między sznurami idą przez NODE_AXIS
- nie ma bezpośrednich losowych połączeń A↔B↔C↔D
- izometria każdego sznura zachowana

---

## FIGURY REZONANSOWE

### TRÓJKĄT (potrójne połączenia)
Wybór trzech sznurów, np.:

- A, B, C

Relacje:
- R_AB_axis
- R_BC_axis
- R_CA_axis

Powstaje:
- figura trójkątna
- 3 cykle współrezonujące
- 3 procesory w sprzężeniu

### TETRAGON (poczwórne połączenia)
Wszystkie cztery sznury:

- A, B, C, D

Relacje:
- R_AB_axis
- R_BC_axis
- R_CD_axis
- R_DA_axis
- relacje przekątne przez NODE_AXIS

Powstaje:
- pełna kwadratura (tetragon skrętu)
- 4 cykle współrezonujące
- pełna architektura 4 procesorów

---

## POJEMNOŚĆ OPERACYJNA

Założenie:
- 32 wejściowe „bity” (skręty) na CPU

Dla jednego CPU:
- 32 wejścia × 48 pozycji = 1536 stanów operacyjnych

Dla 4 CPU:
- 4 × 1536 = 6144 stanów operacyjnych

Z figurami:
- trójkąt/tetragon dodają relacje między cyklami
- efektywna pojemność rośnie przez relacje, nie przez długość sznura

---

## FLOW (przepływ w architekturze 4 CPU)

1. CPU_X (A/B/C/D) pobiera word16
2. DETECT_SCREW -> S_X
3. DERIVE_DIRECTION -> K_X
4. TIMDR waliduje S_X/K_X (globalnie)
5. EMIT_INDEX -> idx_X
6. LUT256[idx_X] -> NODE_X
7. NODE_X trafia do ROPE48_X (na odpowiednią warstwę/pozycję)
8. GIPU aktualizuje relacje w ROPE48_X
9. NODE_AXIS spina sznury (trójkąt/tetragon)
10. VISUAL_ENGINE tworzy obraz figur (trójkąt/tetragon)
11. MONITOR_SCREW_FILTERS wyświetla:
    - skręt
    - kierunek
    - warstwy
    - relacje
    - figury (trójkąt/tetragon)

---

## WŁAŚCIWOŚCI ARCHITEKTURY 4 CPU

- każdy sznur zachowuje izometrię (4×12 = 48)
- nie wydłużamy sznura ponad warunek brzegowy
- zwiększamy zdolność przez:
  - liczbę sznurów (4)
  - figury połączeń (trójkąt/tetragon)
  - relacje osiowe
- pojemność rośnie topologicznie, nie bitowo
- system „myśli” w figurach, nie w liniach


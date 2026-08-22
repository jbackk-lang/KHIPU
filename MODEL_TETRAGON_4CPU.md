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

**TRÓJKĄT** (CPU A, B, C): relacje `R_AB_axis, R_BC_axis, R_CA_axis`.
Efekt: 3 cykle współrezonujące, propagacja ΔS przez trzy węzły.

**TETRAGON** (CPU A, B, C, D): relacje `R_AB_axis, R_BC_axis, R_CD_axis,
R_DA_axis` + przekątne `R_AC_axis, R_BD_axis`. Efekt: pełna kwadratura,
4 cykle współrezonujące, propagacja ΔS przez całą figurę.

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

Decyzje interpretacyjne specyficzne dla tego modułu (poza tymi
opisanymi w `MODEL_PC.md` §10):

- **Agregacja NODE_AXIS z 3–4 węzłów CPU** — nie podano wzoru; przyjęto
  głosowanie większościowe (moda) na każdej osi osobno (`axis.py`).
- **Zakres wzrostu pojemności dla figur** — dokumentacja podaje widełki
  (trójkąt +15–20%, tetragon +30–40%) bez jednej liczby; kod zwraca
  `(min, max, środek)` zamiast jednej wartości, żeby nie zgadywać na siłę.

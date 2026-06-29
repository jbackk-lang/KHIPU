# MODEL_PC_TOPLOGIC
Topologiczny model PC oparty na skręcie, kierunku, sznurze i filtrach obrazowania.

---

## CPU_CORE_16
Procesor 16-bitowy odpowiedzialny wyłącznie za wyznaczanie skrętu i kierunku.

### Operacje:
- DETECT_SCREW(word16) -> S ∈ {S+, S−, S0, S↑, S↓, S×, S!}
- DERIVE_DIRECTION(S) -> K ∈ {K→, K←, K↻, K↺, Kφ}
- EMIT_INDEX(S,K) -> idx ∈ [0..255]

### Zasady:
- Skręt jest nadrzędny.
- Kierunek jest deterministyczną funkcją skrętu.
- CPU nie liczy drogi, brzegu, warstw ani relacji.

---

## MEMORY_CORE (ROPE_MEMORY)
Pamięć sznurkowa przechowująca pełne stany topologiczne.

### Struktura NODE256:
- skręt: S
- kierunek: K
- droga: D ∈ {D0, D1, D2, DM, DT, DW}
- brzeg: B ∈ {B0, B1, BM, BT}
- szerokość: W ∈ {W0, W±, Wφ, WM, WT}
- warstwa: L ∈ {L1, L2, LM, LT}
- relacje: R ∈ {R=, R×, R⊕, R⊗, R0}

### LUT256:
- wejście: idx = (S,K)
- wyjście: NODE256
- modyfikowalna przez TIMDR i GIPU

### ROPE256 (sznur):
- lista NODE256 w kolejności czasowej
- relacje globalne:
  - odległości
  - sprzężenia
  - rezonanse
  - przejścia warstw
- walidacja globalna:
  - zgodność skrętu
  - zgodność kierunku
  - spójność przebiegu

---

## VALIDATION_LAYER
Warstwa walidacji modelu.

### TIMDR:
- walidacja skrętu
- walidacja kierunku
- pilnowanie φ i zasady 1/2
- może wymusić odwrócenie skrętu

### GIPU:
- zarządzanie sznurem ROPE256
- walidacja węzłów, odległości, przejść warstw
- aktualizacja LUT256

---

## VISUAL_ENGINE (obrazowanie)
Silnik obrazowania korzystający z tych samych danych co CPU i pamięć.

### Tryby:
#### PROJECTION_2D:
- skręt -> kolor
- kierunek -> wektor
- droga -> kształt
- brzeg -> obramowanie
- warstwa -> głębokość
- relacje -> linie łączące

#### PROJECTION_3D:
- skręt -> rotacja
- kierunek -> orientacja
- droga -> trajektoria
- brzeg -> powierzchnia
- warstwa -> poziom
- relacje -> siatka połączeń

### Wejście:
- ROPE256
- LUT256

### Wyjście:
- FRAME:
  - obraz 2D/3D
  - mapa skrętu
  - mapa kierunku
  - mapa warstw
  - mapa relacji

### FRAME_BUFFER:
- przechowuje ostatnie N klatek
- umożliwia analizę zmian sznura

---

## MONITOR_SCREW_FILTERS
Filtry skrętowe wymagane przed produkcją monitorów.

### Filtry:
- S-FILTER (skręt):
  - rozróżnia S+, S−, S0, S↑, S↓, S×, S!
  - zamienia skręt na rotację/kolor/głębokość

- K-FILTER (kierunek):
  - stabilizuje orientację
  - nie gubi wektorów

- L-FILTER (warstwy):
  - separuje poziomy topologiczne
  - zapobiega nakładaniu

- B-FILTER (brzegi):
  - wyświetla brzeg zgodnie z topologią

- R-FILTER (relacje):
  - pokazuje linie, sprzężenia, rezonanse

### Matryca monitora:
- RGB + warstwa skrętu + warstwa kierunku + warstwa warstw + warstwa brzegów + warstwa relacji

---

## FLOW (przepływ danych)
1. CPU_CORE_16 pobiera word16
2. DETECT_SCREW -> S
3. DERIVE_DIRECTION -> K
4. TIMDR waliduje (S,K)
5. EMIT_INDEX -> idx
6. LUT256[idx] -> NODE256
7. NODE256 trafia do ROPE256
8. GIPU aktualizuje relacje
9. VISUAL_ENGINE tworzy FRAME
10. MONITOR_SCREW_FILTERS wyświetla FRAME

---

## WŁAŚCIWOŚCI SYSTEMU
- skręt jest nadrzędny
- kierunek wynika ze skrętu
- topologia siedzi w pamięci, nie w CPU
- kompresja jest skutkiem hierarchii
- walidacja jest wbudowana (TIMDR + GIPU)
- obrazowanie jest projekcją sznura
- monitor musi mieć filtry skrętowe


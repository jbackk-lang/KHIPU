# MODEL_PC — architektura jednoprocesorowa

> **[POCHODZENIE]** Rozwinięcie koncepcji zapoczątkowanej w osobnym repo
> [jbackk-lang/PC_TIMDR](https://github.com/jbackk-lang/PC_TIMDR)
> (State9/F4-RED, 252 stany) - tamto repo jest teraz archiwum, dalszy
> rozwój (włącznie z rozszerzeniem do 4 CPU, patrz `MODEL_TETRAGON_4CPU.md`)
> jest tutaj.


Scalony dokument. Zastępuje: `modelPC.md`, `MODEL_PC_TOPLOGIC.md`,
`MODEL_PC_MEMORY.md`, `MODEL_PC_VISUAL.md`, `NODE256.md`, `ROPE256`,
`MODEL_PC_IO`, `COMPRESSOR256.md`, `SPECYFIKACJA_KOMPRESORA_TOPOLOGICZNEGO.md`
— te pliki opisywały tę samą architekturę we fragmentach, w dużej części
dosłownie się powielając. Mapowanie starych plików na ten dokument jest
w `REORGANIZACJA.md`.

Model topologiczny PC oparty na skręcie, kierunku, sznurze i filtrach
obrazowania — jeden procesor, jedna pamięć sznurkowa, jedna warstwa
walidacji, jeden silnik obrazowania.

---

## 1. CPU_CORE_16

Procesor 16-bitowy odpowiedzialny wyłącznie za wyznaczanie skrętu
i kierunku dla każdego słowa danych. Nie liczy drogi, brzegu, warstw
ani relacji — to robi pamięć (LUT256 + GIPU).

Operacje:
- `DETECT_SCREW(word16) -> S`, gdzie `S ∈ {S+, S−, S0, S↑, S↓, S×, S!}`
- `DERIVE_DIRECTION(S) -> K`, gdzie `K ∈ {K→, K←, K↻, K↺, Kφ}`
- `EMIT_INDEX(S,K) -> idx ∈ [0..255]`

Zasady:
- skręt jest nadrzędny i pierwszy,
- kierunek jest deterministyczną funkcją skrętu (patrz tabela w §5),
- CPU nie przechowuje danych.

## 2. NODE256 — pełny stan topologiczny

Hierarchia atrybutów węzła (każdy „wynika” z poprzedniego):

| Warstwa | Symbol | Domena |
|---|---|---|
| skręt | S | `S+, S−, S0, S↑, S↓, S×, S!` |
| kierunek | K | `K→, K←, K↻, K↺, Kφ` |
| droga | D | `D0, D1, D2, DM, DT, DW` |
| brzeg | B | `B0, B1, BM, BT` |
| szerokość | W | `W0, W±, Wφ, WM, WT` |
| warstwa | L | `L1, L2, LM, LT` |
| relacje | R | `R=, R×, R⊕, R⊗, R0` |

## 3. LUT256 (tablica stanów)

- wejście: `idx = EMIT_INDEX(S,K)`
- wyjście: pełny `NODE256`
- modyfikowalna przez TIMDR (korekta S/K) i GIPU (relacje R)

## 4. ROPE256 (sznur pamięci)

- lista NODE256 w kolejności czasowej
- relacje globalne: odległości, sprzężenia, rezonanse, przejścia warstw
- walidacja globalna: zgodność skrętu, zgodność kierunku, spójność przebiegu

## 5. VALIDATION_LAYER

**TIMDR** — globalny walidator skrętu/kierunku:
- akceptuje lub odrzuca parę (S,K),
- pilnuje „zasady 1/2 i φ”,
- może wymusić korektę S/K.

Jedyna jawnie podana reguła wyprowadzenia K ze S:

| S | K |
|---|---|
| S+ | K→ |
| S− | K← |
| S↑ | K↻ |
| S↓ | K↺ |
| S0 | Kφ |

**GIPU** — globalny integrator sznura:
- zarządza ROPE256 (węzły, odległości, przejścia warstw),
- aktualizuje relacje R,
- modyfikuje LUT256.

## 6. COMPRESSOR256 (kompresja)

```
bajt -> stan topologiczny (NODE256)
klasyfikacja po skręcie
redukcja po: kierunku, drodze, brzegu, szerokości, warstwie, relacjach
walidacja: TIMDR (skręt/kierunek), GIPU (sznur, węzły, odległości)
wyjście: stan skompresowany  ALBO  stan pełny (jeśli walidacja odrzuci)
```

## 7. VISUAL_ENGINE (obrazowanie)

Wejście: ROPE256 + LUT256. Wyjście: `FRAME`.

| Tryb | skręt | kierunek | droga | brzeg | warstwa | relacje |
|---|---|---|---|---|---|---|
| PROJECTION_2D | kolor | wektor | kształt | obramowanie | głębokość | linie łączące |
| PROJECTION_3D | rotacja | orientacja | trajektoria | powierzchnia | poziom | siatka połączeń |

`FRAME_BUFFER` przechowuje ostatnie N klatek, umożliwia analizę zmian sznura.

### MONITOR_SCREW_FILTERS

Filtry wymagane przed produkcją obrazu: S-FILTER, K-FILTER, L-FILTER,
B-FILTER, R-FILTER. Matryca monitora: RGB + warstwa skrętu + warstwa
kierunku + warstwa warstw + warstwa brzegów + warstwa relacji.

## 8. FLOW (przepływ danych)

```
1. CPU_CORE_16 pobiera word16
2. DETECT_SCREW      -> S
3. DERIVE_DIRECTION  -> K
4. TIMDR waliduje (S,K)
5. EMIT_INDEX        -> idx
6. LUT256[idx]        -> NODE256
7. NODE256 -> ROPE256
8. GIPU aktualizuje relacje
9. VISUAL_ENGINE tworzy FRAME
10. MONITOR_SCREW_FILTERS wyświetla FRAME
```

## 9. WŁAŚCIWOŚCI SYSTEMU

- skręt jest nadrzędny wobec wszystkich operacji,
- kierunek jest funkcją skrętu, nie osobnym wyborem,
- topologia (D, B, W, L, R) siedzi w pamięci (LUT256/GIPU), nie w CPU,
- kompresja jest skutkiem hierarchii, nie osobnym algorytmem,
- walidacja jest wbudowana (TIMDR + GIPU).

---

## 10. Status implementacji

Zaimplementowane w `khipu/` (moduł `khipu.pipeline.SingleCPUSystem`
spina wszystko poniżej w jeden `FLOW`):

| Element specyfikacji | Moduł | Uwagi |
|---|---|---|
| CPU_CORE_16 | `khipu/cpu.py` | patrz „Decyzje interpretacyjne” niżej |
| NODE256 | `khipu/node256.py` | pełna walidacja domen |
| LUT256 | `khipu/lut256.py` | deterministyczne wypełnienie domyślne |
| ROPE256 | `khipu/rope.py` | |
| TIMDR | `khipu/timdr.py` | „zasada 1/2 i φ” zinterpretowana liczbowo |
| GIPU | `khipu/gipu.py` | reguła relacji R zinterpretowana |
| COMPRESSOR256 | `khipu/compressor.py` | run-length po pełnej krotce (S,K,D,B,W,L,R) |
| VISUAL_ENGINE / FRAME_BUFFER | `khipu/visual.py` | FRAME jako dane, bez renderowania pikseli |
| MONITOR_SCREW_FILTERS | — | niezaimplementowane (wymaga wyboru biblioteki graficznej) |

### Naprawione błędy wydajności i poprawności (2026-08)

Uruchomienie realnej symulacji (`SingleCPUSystem`/`TetragonSystem` na
setkach tysięcy słów) ujawniło trzy błędy niewidoczne przy 56 testach
jednostkowych operujących na małych, statycznych listach:

1. **O(n²) w `GIPU.update_relations()`** — `SingleCPUSystem.feed()`
   przeliczał relacje dla CAŁEJ historii sznura przy każdym pojedynczym
   słowie. Zmierzone: 4394 słów/s przy N=500, tylko 793 słów/s przy
   N=3000 (kwadratowa degradacja), 200 000 słów nie kończyło się w
   2 minuty. **Naprawione**: nowa metoda `GIPU.extend_relations()`
   liczy tylko jedną, nową krawędź na dodane słowo — O(1) na słowo,
   O(n) łącznie. Dodatkowa korzyść: usuwa też błąd POPRAWNOŚCI, bo stara
   metoda traktowała rosnący, otwarty `Rope256` jako sznur ZAMKNIĘTY
   (modulo długości), więc relacja danego węzła zmieniała się przy
   każdym kolejnym słowie, zamiast być ustalona raz na zawsze.
2. **O(n²) w `VisualEngine.project()`** — ta sama choroba: pełna
   projekcja całej historii sznura na każde słowo. **Naprawione**:
   `SingleCPUSystem.feed()` przekazuje teraz tylko okno ostatnich
   `frame_buffer_size` węzłów (i tak tylko tyle klatek zachowuje
   `FrameBuffer`).
3. Po obu naprawach zmierzona przepustowość jest STAŁA niezależnie od
   długości sznura: ~50 000-56 000 słów/s (dawniej degradowała się do
   setek/s po kilku tysiącach słów).

**Znany, jeszcze NIE naprawiony problem**: `LUT256.lookup()`
cache'uje i zwraca TEN SAM obiekt `Node256` dla każdego wystąpienia
danego `idx` — a realnych par (S,K)/idx jest tylko 7 (patrz niżej), więc
cały sznur, niezależnie od długości, składa się z odwołań do co najwyżej
7 współdzielonych, MUTOWALNYCH obiektów, nie z niezależnych węzłów.
Zmiana `.r` na "jednym" wystąpieniu zmienia je jednocześnie na
wszystkich innych pozycjach sznura o tym samym idx. To głębszy problem
niż wydajność — dotyczy poprawności całego modelu pamięci sznura.

### Decyzje interpretacyjne

Oryginalna dokumentacja opisuje architekturę na poziomie koncepcyjnym,
bez części algorytmów bitowych. Żeby powstał uruchamialny, testowalny
kod, trzeba było dokonać kilku konkretnych wyborów — każdy jest
oznaczony komentarzem `DECYZJA INTERPRETACYJNA` w kodzie źródłowym:

- **`DETECT_SCREW(word16) -> S`** — nie było podanego algorytmu bitowego,
  tylko domena wyjściowa. Przyjęto deterministyczne mapowanie oparte na
  liczbie jedynek w starszym/młodszym bajcie i najstarszym bicie
  (`khipu/cpu.py`). Do podmiany bez wpływu na resztę systemu.
- **`EMIT_INDEX(S,K) -> idx`** — skoro K jest funkcją S, realnych par
  (S,K) jest tylko 7, więc `idx` to stabilny indeks pary w ustalonym
  porządku, mieszczący się w [0,255] (`khipu/cpu.py`).
- **Domyślne D/B/W/L/R w LUT256** — nie podano reguły przypisania;
  przyjęto deterministyczną funkcję `idx` (`khipu/lut256.py`).
- **„Zasada 1/2 i φ” w TIMDR** — zinterpretowana jako: udział węzłów
  „rosnących” (S+, S↑) w sznurze musi mieścić się w `[0.5 - (φ-1), 0.5 + (φ-1)]`
  (`khipu/timdr.py`).
- **Reguła relacji R w GIPU** — nie podano wzoru; przyjęto regułę opartą
  wprost na nazwach relacji (ten sam S i K → rezonans, itd.) w `khipu/gipu.py`.
- **Paleta skręt→kolor w VISUAL_ENGINE** — dokumentacja mówi tylko
  „skręt → kolor” bez wartości RGB; przyjęto jedną stałą paletę
  (`khipu/visual.py`).

Jeśli któraś z tych decyzji nie odpowiada oryginalnemu zamysłowi, każda
jest zlokalizowana w jednym miejscu w kodzie i nie wpływa na resztę
pipeline'u (interfejsy między modułami nie zależą od konkretnych reguł).

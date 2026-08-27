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

**Naprawiony błąd poprawności — aliasing obiektów w LUT256 (2026-08)**:
`LUT256.lookup()` cache'owało i zwracało TEN SAM obiekt `Node256` dla
każdego wystąpienia danego `idx` — a realnych par (S,K)/idx jest tylko 7
(patrz niżej), więc cały sznur, niezależnie od długości, składał się
z odwołań do co najwyżej 7 współdzielonych, MUTOWALNYCH obiektów, nie
z niezależnych węzłów. Zmiana `.r` na "jednym" wystąpieniu zmieniała je
jednocześnie na wszystkich innych pozycjach sznura o tym samym idx.
Potwierdzone empirycznie przed naprawą: 10 słów -> 4 unikalne idx ->
tylko 4 unikalne obiekty (zamiast 10 niezależnych węzłów), `.r` identyczne
na wszystkich pozycjach dzielących idx niezależnie od ich rzeczywistego
sąsiedztwa w sznurze. **Naprawione**: `lookup()` zwraca teraz kopię
(`dataclasses.replace()`), `set()` przyjmuje i przechowuje kopię
przekazanego węzła — LUT256 nadal działa jako jeden kanoniczny szablon na
`idx` (determinizm zachowany), ale każda pozycja w ROPE256/ROPE48 ma
odtąd własny, niezależny obiekt. Zweryfikowane ponownie na tym samym
przykładzie (10 słów -> 10 niezależnych obiektów) oraz stress-testem na
300 000 słów (300 000 niezależnych obiektów, zero aliasingu). Regresyjne
testy tożsamości obiektu: `tests/test_lut256.py::test_lookup_returns_independent_objects`,
`::test_set_stores_independent_copy`.

**Optymalizacja kopiowania w LUT256 (2026-08)**: powyższa poprawka użyła
`dataclasses.replace()`, które odtwarza obiekt przez `__init__` i więc
ponownie waliduje wszystkie 7 pól `Node256.__post_init__()` przy KAŻDEJ
kopii — zmierzony koszt: ~1.9x wolniej niż budowa bez walidacji
(341 275 obj/s vs 637 538 obj/s). Dane kopiowane tu są już znane jako
poprawne, więc rewalidacja to czysty narzut. Zamienione na `copy.copy()`
(płytka kopia — wystarczająca, bo `Node256` ma wyłącznie pola
niemutowalne `str`/`int`), z tą samą gwarancją niezależności obiektów,
bez ponownego wywołania `__post_init__`. Te same testy regresyjne dalej
przechodzą.

**Wsadowa (wektorowa) klasyfikacja (2026-08)**: `khipu/cpu.py` ma teraz
`CPUCore16.detect_screw_batch()` / `derive_direction_batch()` /
`emit_index_batch()` / `classify_batch()` — numpy'owe odpowiedniki
DETECT_SCREW/DERIVE_DIRECTION/EMIT_INDEX dla całych tablic word16
naraz (opcjonalna zależność, rzuca `ImportError` przy wywołaniu bez
numpy, moduł importuje się bez numpy normalnie). Zweryfikowane krzyżowo
ze skalarną implementacją na całej 16-bitowej przestrzeni (65536 wartości,
0 rozbieżności) i na losowych próbkach `hypothesis`
(`tests/test_cpu_vectorized.py`, `tests/test_properties.py`). Zmierzone:
7 497 594 słów/s (wektorowo) vs 627 174 słów/s (skalarnie w pętli) —
12x szybciej DLA SAMEJ KLASYFIKACJI. **Uczciwe zastrzeżenie**: to NIE
przyspiesza `SingleCPUSystem.feed_many()` w tej samej proporcji, bo
klasyfikacja to ok. 5.5% czasu pełnego `feed()` na słowo (1.6 μs z ok.
29 μs) — reszta (LUT/ROPE/GIPU/VisualEngine) jest z definicji
sekwencyjna (każdy krok zależy od stanu zbudowanego przez poprzednie).
Realna wartość: szybka, bezstanowa analiza masowa (np. rozkład S/K
w dużym pliku danych) bez kosztu budowania pełnej symulacji.

### Audyt "numerologia vs realna matematyka" (2026-08)

Zastosowano protokół z `timdr-signal-framework` §18 (zdefiniuj obiekt i
metrykę PRZED uruchomieniem, uruchom raz, zgłoś wynik uczciwie) do
DETECT_SCREW i "zasady 1/2 i φ" w TIMDR — obu miejsc w kodzie, gdzie φ
pojawia się jako liczba mająca coś "znaczyć". Wynik: **dwa konkretne,
wcześniej niewykryte błędy martwego kodu**, nie kwestia interpretacji:

1. **`S.BANG` ("S!") było matematycznie nieosiągalne.** Stary tiebreak
   przy remisie wagi bitowej (`pop_hi == pop_lo`) sprawdzał parzystość
   sumy `pop_hi + pop_lo` — a suma dwóch RÓWNYCH liczb jest zawsze
   parzysta, z definicji, niezależnie od konkretnych bitów. Potwierdzone
   wyczerpującym przeglądem całej przestrzeni 16-bitowej: 0/65536
   wystąpień `S.BANG` przed naprawą. Naprawione (tiebreak = identyczność
   bajtów `hi == lo` zamiast parzystości sumy): po naprawie `S.TIMES`
   255/65536 (0.39%), `S.BANG` 12614/65536 (19.25%) — obie gałęzie
   faktycznie osiągalne. Patrz `khipu/cpu.py` docstring "NAPRAWIONY
   MARTWY WARIANT".
2. **Domyślna tolerancja `φ-1≈0.618` w `TIMDRValidator.validate_rope()`
   była matematycznie niezdolna do zwrócenia `False`.** `balance` (udział
   węzłów "rosnących") jest ułamkiem w `[0,1]`, więc `|balance-0.5|` nigdy
   nie przekracza `0.5` — a `0.5 < φ-1`, więc walidacja PRZECHODZI zawsze,
   dla dowolnych danych, łącznie ze sznurem złożonym w 100% z jednego
   kierunku. Dodatkowo `validate_rope()`/`rope_balance()` nie są wołane
   przez żaden inny moduł w działającym pipeline — ta "walidacja
   globalna" była podwójnie martwa: nieużywana ORAZ, gdyby użyta,
   bezwarunkowo zawsze prawdziwa. Naprawione: tolerancja to teraz
   `2-φ=1/φ²≈0.382` (też liczba wprost z φ, przez tożsamość `φ²=φ+1`),
   która jest mniejsza od 0.5 i faktycznie potrafi odrzucić skrajny
   sznur. Patrz `khipu/timdr.py` docstring "NAPRAWIONA TOLERANCJA MARTWA".

**Zweryfikowane empirycznie** (nie tylko dowód analityczny): 200 000
losowych realnych słów przez pełny pipeline daje `balance≈0.501`
(przechodzi, jak powinno), sztucznie skrajny sznur teraz poprawnie NIE
przechodzi z domyślną tolerancją. Regresje:
`tests/test_cpu.py::test_bang_is_reachable`,
`tests/test_timdr.py::test_default_tolerance_can_actually_reject_extreme_rope`.

**Uczciwe podsumowanie audytu**: to NIE jest przypadek "wzór z φ okazał
się fałszywym wzorcem" (jak w przypadkach z `timdr-signal-framework` §18
dotyczących π/φ/liczb pierwszych) — φ tu nigdy nie miało być odkrytym
wzorcem, tylko interpretacją niedookreślonej specyfikacji ("zasada 1/2 i
φ" bez podanego wzoru, jawnie oznaczone `DECYZJA INTERPRETACYJNA` od
początku). Problem był węższy i bardziej konkretny: SPOSÓB użycia φ (jako
tolerancji WIĘKSZEJ od możliwego zakresu) czynił regułę martwą niezależnie
od tego, czy φ "naprawdę coś znaczy" w tym kontekście — a to samo w sobie
jest wykrywalnym błędem, nie kwestią gustu interpretacyjnego.

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

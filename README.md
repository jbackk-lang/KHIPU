# KHIPU

> **[POCHODZENIE]** Model 1-procesorowy w tym repo (`MODEL_PC.md`,
> `khipu/pipeline.py::SingleCPUSystem`) rozwija koncepcję, która
> zaczęła się w osobnym, wcześniejszym repozytorium
> **[jbackk-lang/PC_TIMDR](https://github.com/jbackk-lang/PC_TIMDR)**
> (tam: State9/F4-RED, 252 stany). PC_TIMDR zostało porzucone na rzecz
> tego repo, m.in. dlatego że dopiero tutaj powstało **rozszerzenie do
> 4 procesorów** (`MODEL_TETRAGON_4CPU.md`, `khipu/tetragon.py`) - PC_TIMDR
> nigdy takiego rozszerzenia nie miało. PC_TIMDR ma teraz w swoim README
> notatkę odsyłającą tutaj, dla porządku ta notatka działa też w drugą
> stronę.

Pismo węzełkowe a kod binarny — repozytorium łączy trzy warstwy:

1. **Działający kod** (`khipu/`) — implementacja architektury opisanej
   w dokumentach niżej: procesor topologiczny, pamięć sznurkowa (ROPE),
   walidacja (TIMDR/GIPU), kompresor, silnik obrazowania — od 1 CPU
   (`MODEL_PC.md`) do 4 CPU w figurze rezonansowej (`MODEL_TETRAGON_4CPU.md`).
2. **Koncepcja khipu jako formalizm operatorowy** (`KHIPU_KONCEPCJA.md`) —
   autorska rama pojęciowa łącząca inkaskie sznury węzełkowe z modelem
   procesora powyżej.
3. **Hipoteza historyczna** (`HIPOTEZA_ECHO_OSI.md`) — niezweryfikowane
   twierdzenie o globalnym przesunięciu osi i „echu” 12 800–11 000 lat
   temu, jawnie oznaczone jako hipoteza, nie fakt.

Te trzy warstwy są rozdzielone celowo — (1) da się uruchomić i przetestować,
(2) jest spójną wewnętrznie ramą pojęciową, (3) jest niepotwierdzonym
twierdzeniem o świecie rzeczywistym. Mieszanie ich w jednym dokumencie
utrudniało odróżnienie, co jest czym.

## Eksperyment: State9/GIPU jako moduł sieci neuronowej

Osobne repo **[jbackk-lang/KHIPU-NEURAL](https://github.com/jbackk-lang/KHIPU-NEURAL)**
testuje, czy State9/F4-RED i regułę relacji GIPU da się przełożyć na
uczony (gradientowy) moduł sieci neuronowej, zamiast deterministycznej
symulacji jak tutaj. Wynik jest **uczciwie negatywny**: na zadaniu
zaprojektowanym wprost pod regułę GIPU, generyczny MLP bije architekturę
inspirowaną KHIPU (test MAE 0.365 vs 1.08, przy trywialnym predyktorze
średniej = 1.03). Osobne repo, bo inna domena (trening gradientowy) niż
czysto deterministyczna symulacja tutaj — nie miesza się w trójwarstwową
strukturę tego repo (kod / koncepcja / hipoteza).

## Dokumentacja

| Plik | Zawartość |
|---|---|
| `MODEL_PC.md` | pełna architektura jednoprocesorowa (CPU, NODE256, LUT256, ROPE256, TIMDR/GIPU, kompresor, obrazowanie) + status implementacji |
| `MODEL_TETRAGON_4CPU.md` | architektura 4-procesorowa (ROPE48, NODE_AXIS, figury rezonansowe, pojemność operacyjna) + status implementacji |
| `KHIPU_KONCEPCJA.md` | formalizm operatorowy τ/J/Λ łączący khipu z modelem procesora — oznaczony jako autorska koncepcja |
| `HIPOTEZA_ECHO_OSI.md` | hipoteza o przesunięciu osi/echu — oznaczona jako niezweryfikowana |
| `REORGANIZACJA.md` | co się zmieniło względem poprzedniej wersji repo i dlaczego |

## Kod

```
khipu/
    node256.py    NODE256: S, K, D, B, W, L, R
    cpu.py        CPU_CORE_16: DETECT_SCREW, DERIVE_DIRECTION, EMIT_INDEX
    lut256.py     LUT256
    timdr.py      TIMDR (walidacja globalna)
    gipu.py       GIPU (integrator sznura/relacji)
    rope.py       ROPE256 (sznur, model jednoprocesorowy)
    rope48.py     ROPE48 (sznur izometryczny 4x12, model 4-procesorowy)
    compressor.py COMPRESSOR256
    visual.py     VISUAL_ENGINE + FRAME_BUFFER
    axis.py       NODE_AXIS + figury rezonansowe (trójkąt/tetragon)
    tetragon.py   TetragonSystem — pełny model 4 CPU
    pipeline.py   SingleCPUSystem — pełny model 1 CPU
```

Legacy: `node.py` / `rope.py` / `test.py` w katalogu głównym to oryginalny,
prosty format zapisu tekstowego (CTX/NODE) — zachowany bez zmian
funkcjonalnych, tylko z dodanymi testami (`tests/test_legacy_rope.py`).

## Szybki start

```bash
pip install pytest
python3 -m pytest tests/ -v      # 62 testy

python3 -c "
from khipu import SingleCPUSystem
sys = SingleCPUSystem()
for w in [0, 1234, 65535]:
    print(sys.feed(w))
"

python3 -c "
from khipu import TetragonSystem
t = TetragonSystem()
for i, cpu in enumerate(['A','B','C','D']):
    t.feed(cpu, (i+1) * 4001)
print('pojemność (min,max,mid):', t.capacity_with_resonance())
print('relacje osiowe:', t.axial_relations())
"
```

## Status

Cały pipeline opisany w `MODEL_PC.md` i `MODEL_TETRAGON_4CPU.md` jest
zaimplementowany i pokryty testami (62/62 przechodzi). Kilka miejsc
w oryginalnej specyfikacji było niejednoznacznych (brak konkretnego
algorytmu bitowego, brak wzoru na niektóre reguły) — każde takie miejsce
jest oznaczone w kodzie jako `DECYZJA INTERPRETACYJNA` i opisane w sekcji
„Status implementacji” odpowiedniego dokumentu modelu.

Stress-test na dużą skalę (2026-08, po naprawie błędu aliasingu LUT256
opisanego w `MODEL_PC.md`): 300 000 słów przez `SingleCPUSystem` (brak
aliasingu obiektów węzłów, przepustowość stabilna ~39 000 słów/s, bez
degradacji na żadnym z pięciu kolejnych okien po 50 000 słów) i 200 000
słów przez `TetragonSystem` (4 CPU, ~13 000 słów/s na CPU, stabilne w
czasie, `Rope48` poprawnie zawija się jako pierścień FIFO bez błędów na
setkach tysięcy wywołań `push()` na rdzeń). Przypadki brzegowe (pusty
sznur, pojedynczy węzeł, nieznana nazwa CPU, `word16` poza zakresem
16-bit) obsłużone bez wyjątków ani cichych błędów.

MONITOR_SCREW_FILTERS (faktyczny rendering obrazu z FRAME) nie jest
zaimplementowany — FRAME zawiera wszystkie dane potrzebne do tego kroku,
ale wybór biblioteki graficznej pozostawiono na później.

## Licencja

MIT — patrz `LICENSE`.

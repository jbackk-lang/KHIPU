# Reorganizacja repozytorium — mapowanie starych plików na nowe

Ten plik dokumentuje, co się zmieniło względem poprzedniej wersji repo,
żeby zmiany dało się zweryfikować przed scaleniem z prawdziwym repo na
GitHubie (ten agent nie ma dostępu do Twojego konta GitHub — wszystkie
pliki są dostarczone lokalnie do ręcznego wgrania/commitu).

## Scalone dokumenty (duplikacja → jeden plik)

| Stare pliki | Nowy plik | Powód |
|---|---|---|
| `modelPC.md`, `MODEL_PC_TOPLOGIC.md`, `MODEL_PC_MEMORY.md`, `MODEL_PC_VISUAL.md`, `NODE256.md`, `ROPE256`, `MODEL_PC_IO`, `COMPRESSOR256.md`, `SPECYFIKACJA_KOMPRESORA_TOPOLOGICZNEGO.md` | `MODEL_PC.md` | 9 plików opisywało tę samą architekturę jednoprocesorową na różnych poziomach szczegółowości, w dużej mierze się dosłownie powielając (np. `NODE256.md` i `ROPE256` to podzbiory `MODEL_PC_TOPLOGIC.md`) |
| stary `MODEL_TETRAGON_4CPU.md`, `RESONANCE_COMM.md`, sekcje architektoniczne starego `README.md` | `MODEL_TETRAGON_4CPU.md` (nowa treść) | `README.md` był w praktyce sklejeniem tamtych dwóch plików niemal 1:1 |

## Podzielone dokumenty (jeden plik → kilka, po temacie)

| Stary plik | Nowe pliki | Powód |
|---|---|---|
| `pismowęzęłkowe.md` | `KHIPU_KONCEPCJA.md` (formalizm operatorowy) + `HIPOTEZA_ECHO_OSI.md` (twierdzenia historyczne o przesunięciu osi/echu) | oryginalny plik mieszał autorski formalizm pojęciowy z niepopartymi źródłowo twierdzeniami historycznymi podanymi jako fakt; rozdzielenie pozwala oznaczyć część historyczną jako jawną hipotezę, nie zmieniając treści formalizmu |

## Przepisany od zera

| Plik | Zmiana |
|---|---|
| `README.md` | krótki indeks + status implementacji, zamiast pełnej kopii treści `MODEL_TETRAGON_4CPU.md`/`RESONANCE_COMM.md` |

## Nowy kod

| Katalog | Zawartość |
|---|---|
| `khipu/` | implementacja całego pipeline'u opisanego w `MODEL_PC.md` i `MODEL_TETRAGON_4CPU.md` — wcześniej te dokumenty nie miały żadnej odpowiadającej im implementacji (istniały tylko `node.py`/`rope.py`/`test.py`, czyli osobny, dużo prostszy format zapisu tekstowego, niepowiązany z NODE256/LUT256/TIMDR/GIPU) |
| `tests/` | 56 testów pytest pokrywających `khipu/` oraz (jako `test_legacy_rope.py`) oryginalny `node.py`/`rope.py` |

## Bez zmian

`node.py`, `rope.py`, `test.py` w katalogu głównym, `LICENSE` — zachowane
w oryginalnej postaci (kod działał poprawnie, dodano tylko realne testy
w `tests/test_legacy_rope.py`, bo oryginalny `test.py` tylko drukował
wynik bez żadnej asercji).

## Jak to wdrożyć w prawdziwym repo

1. Sprawdź `MODEL_PC.md`, `MODEL_TETRAGON_4CPU.md`, `KHIPU_KONCEPCJA.md`,
   `HIPOTEZA_ECHO_OSI.md`, `README.md` — czy scalona treść niczego nie
   zgubiła względem oryginałów.
2. Jeśli tak — usuń stare pliki wymienione w tabelach wyżej z prawdziwego
   repo i wgraj nowe wraz z katalogami `khipu/` i `tests/`.
3. `python3 -m pytest tests/ -v` powinno dać `56 passed`.

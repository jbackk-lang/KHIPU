"""
lut256.py — LUT256 (modelPC.md, MODEL_PC_MEMORY.md, MODEL_PC_TOPLOGIC.md).

    LUT256[idx] -> NODE256

Wejście: idx = EMIT_INDEX(S,K). Wyjście: pełny stan topologiczny NODE256
(z domyślnie przypisanymi D/B/W/L/R). Modyfikowalna przez TIMDR i GIPU.
"""

import copy

from .node256 import Node256, D, B, W, L, R, derive_direction


class LUT256:
    """
    256-slotowa tablica idx -> Node256.

    DECYZJA INTERPRETACYJNA: dokumentacja nie podaje, w jaki sposób LUT256
    dobiera domyślne D/B/W/L/R dla danego idx — mówi tylko, że to LUT
    "zwraca pełny stan topologiczny" i że jest modyfikowalna przez
    TIMDR/GIPU. Domyślne wypełnienie tablicy jest tu deterministyczną
    funkcją idx (żeby dwa uruchomienia dawały ten sam wynik), a nie
    losowaniem — tak, aby cały system był powtarzalny i testowalny.
    TIMDR i GIPU mogą nadpisać dowolny wpis w trakcie działania
    (patrz timdr.py, gipu.py).

    POPRAWKA BŁĘDU ALIASINGU (2026-08, wykryta stress-testem na dużą skalę —
    patrz README.md "Status implementacji"): realnych par (S,K) jest tylko 7,
    więc `idx` powtarza się w kółko dla każdego rosnącego sznura. `lookup()`
    zwracało dawniej BEZPOŚREDNIO obiekt zapisany w `_table[idx]` — więc
    KAŻDE wystąpienie danego idx w ROPE256 było w rzeczywistości tym samym
    obiektem Node256, nie niezależnym węzłem. Skutek: `GIPU.extend_relations()`
    mutujące `.r` na "ostatnim" węźle cicho zmieniało `.r` jednocześnie na
    WSZYSTKICH wcześniejszych pozycjach sznura o tym samym idx (potwierdzone
    empirycznie: 10 słów -> 4 unikalne idx -> tylko 4 unikalne obiekty,
    zamiast 10 niezależnych węzłów). Naprawka: LUT256 przechowuje jeden
    kanoniczny "szablon" na idx (do determinizmu, zgodnie z powyższą decyzją
    interpretacyjną), ale `lookup()` ZWRACA JEGO KOPIĘ, nigdy oryginał — a
    `set()` PRZYJMUJE KOPIĘ zapisywanego węzła, nie referencję do żywego
    obiektu z sznura (bo `GIPU.update_lut()` zapisuje do LUT bezpośrednio
    węzły z ROPE256 — bez kopiowania przy zapisie ten sam problem wracałby
    z drugiej strony). Każda pozycja w ROPE256 ma teraz własny, niezależny
    obiekt Node256 — mutacja jednego węzła nie wpływa już na inne pozycje
    ani na szablon w LUT256. Regresyjny test tożsamości:
    `tests/test_lut256.py::test_lookup_returns_independent_objects`.

    OPTYMALIZACJA KOPIOWANIA (2026-08): pierwsza wersja tej poprawki
    używała `dataclasses.replace()`. `replace()` odtwarza obiekt PRZEZ
    `__init__`, więc na każdym `lookup()`/`set()` ponownie uruchamia całą
    walidację `Node256.__post_init__()` (7 sprawdzeń `in ...ALL`) — zmierzony
    koszt: budowa+walidacja dataclassu jest ~1.9x wolniejsza niż budowa
    bez walidacji (341 275 obj/s vs 637 538 obj/s, ten sam sprzęt/dane).
    Kopiowane tu dane są JUŻ znane jako poprawne (pochodzą z `_default_for()`
    albo z węzła, który sam przeszedł walidację przy tworzeniu) — ponowna
    walidacja przy KAŻDEJ kopii to czysty narzut. `copy.copy()` (płytka
    kopia) daje tę samą gwarancję niezależności obiektów — `Node256` ma
    wyłącznie pola `str`/`int`/`Optional[int]` (niemutowalne), więc płytka
    kopia jest tu równoważna głębokiej — ale NIE wywołuje `__init__`/
    `__post_init__` ponownie. Poprawność bez zmian (te same testy
    identyczności przechodzą), tylko szybciej.
    """

    SIZE = 256

    def __init__(self):
        self._table = {}

    def _default_for(self, idx: int, s: str, k: str) -> Node256:
        d = D.ALL[idx % len(D.ALL)]
        b = B.ALL[idx % len(B.ALL)]
        w = W.ALL[idx % len(W.ALL)]
        l = L.ALL[idx % len(L.ALL)]
        r = R.ALL[idx % len(R.ALL)]
        return Node256(s=s, k=k, d=d, b=b, w=w, l=l, r=r, idx=idx)

    def lookup(self, idx: int, s: str = None, k: str = None) -> Node256:
        if not (0 <= idx <= 255):
            raise ValueError(f"idx poza zakresem [0,255]: {idx}")
        if idx not in self._table:
            if s is None or k is None:
                raise KeyError(
                    f"idx {idx} nie istnieje w LUT256 i nie podano (s,k), "
                    "żeby wygenerować wartość domyślną."
                )
            self._table[idx] = self._default_for(idx, s, k)
        # Kopia, nie oryginał - patrz "POPRAWKA BŁĘDU ALIASINGU" w docstringu klasy.
        # copy.copy() zamiast dataclasses.replace() - patrz "OPTYMALIZACJA KOPIOWANIA".
        return copy.copy(self._table[idx])

    def set(self, idx: int, node: Node256) -> None:
        """Nadpisanie wpisu — używane przez TIMDR (korekta) i GIPU (relacje).

        Przyjmuje KOPIĘ `node`, nie referencję - patrz "POPRAWKA BŁĘDU
        ALIASINGU" w docstringu klasy (GIPU.update_lut() zapisuje tu żywe
        węzły z ROPE256; bez kopiowania przy zapisie dalsza mutacja tego
        węzła w sznurze cicho zmieniałaby też szablon w LUT256)."""
        if not (0 <= idx <= 255):
            raise ValueError(f"idx poza zakresem [0,255]: {idx}")
        self._table[idx] = copy.copy(node)

    def __len__(self):
        return len(self._table)

    def __contains__(self, idx):
        return idx in self._table

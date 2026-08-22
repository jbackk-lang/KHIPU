"""
rope48.py — ROPE48: sznur pojedynczego CPU w architekturze TETRAGON_4CPU
(MODEL_TETRAGON_4CPU.md, RESONANCE_COMM.md).

    4 warstwy x 12 pozycji = 48 węzłów
    długość sznura = 48 (stała, izometria zachowana)
    brzeg domknięty (cykl)

NAPRAWIONY BUG (patrz README.md / MODEL_TETRAGON_4CPU.md "Status
implementacji"): `push()` wcześniej rzucał `OverflowError` po 48. wywołaniu
i trwale blokował dalsze działanie CPU (każdy kolejny `feed()` w
`TetragonSystem` kończył się nieobsłużonym wyjątkiem - system nie mógł
przetworzyć więcej niż 48 słów na rdzeń, 192 łącznie na cały tetragon,
mimo że własny docstring tego modułu od początku obiecywał "sznur
CYKLICZNY"). `push()` jest teraz prawdziwym pierścieniem FIFO: po
zapełnieniu 48 slotów nadpisuje najstarszy wpis, zgodnie z tym, co ten
plik od zawsze deklarował. Długość 48 (4x12) ma znaczenie geometryczne
w architekturze (MODEL_TETRAGON_4CPU.md) i nie jest podnoszona - to nie
jest "za mały limit", tylko brakujące zawijanie. Efekt: brak górnego
limitu liczby słów, jakie CPU może przetworzyć w całym swoim życiu -
sznur zawsze przechowuje 48 najnowszych węzłów.
"""

from typing import List, Optional
from .node256 import Node256

LAYERS = 4
POSITIONS_PER_LAYER = 12
LENGTH = LAYERS * POSITIONS_PER_LAYER  # 48


class Rope48:
    """
    Cykliczny sznur o STAŁEJ długości 48 (izometria warunku brzegowego).
    Sloty puste (jeszcze nieustawione) mają wartość None. Po zapełnieniu
    `push()` nadpisuje najstarszy wpis (prawdziwy pierścień FIFO) -
    nigdy nie rzuca wyjątku z powodu "pełnego" sznura.
    """

    def __init__(self, name: str):
        self.name = name
        self.slots: List[Optional[Node256]] = [None] * LENGTH
        self._write_cursor = 0          # gdzie trafi NASTĘPNY push()
        self.total_pushed = 0           # licznik calego zycia (nie resetuje sie przy zawinieciu)

    def set(self, layer: int, position: int, node: Node256) -> None:
        if not (0 <= layer < LAYERS):
            raise ValueError(f"layer poza zakresem [0,{LAYERS - 1}]: {layer}")
        if not (0 <= position < POSITIONS_PER_LAYER):
            raise ValueError(f"position poza zakresem [0,{POSITIONS_PER_LAYER - 1}]: {position}")
        self.slots[layer * POSITIONS_PER_LAYER + position] = node

    def get(self, layer: int, position: int) -> Optional[Node256]:
        return self.slots[layer * POSITIONS_PER_LAYER + position]

    def push(self, node: Node256):
        """
        Dokłada węzeł w kolejności czasowej. Dopóki sznur nie jest pełny,
        zajmuje kolejny wolny slot (jak dawniej, w porządku _write_cursor).
        Po zapełnieniu wszystkich 48 slotów zawija się i nadpisuje
        NAJSTARSZY wpis (pierścień FIFO wg `_write_cursor`).

        Zwraca nadpisany węzeł (albo None, jeśli nadpisano pusty slot) -
        przydatne, gdyby coś chciało zareagować na "wypadnięcie" najstarszego
        stanu ze sznura (np. logowanie).
        """
        overwritten = self.slots[self._write_cursor]
        self.slots[self._write_cursor] = node
        self._write_cursor = (self._write_cursor + 1) % LENGTH
        self.total_pushed += 1
        return overwritten

    def filled_nodes(self) -> List[Node256]:
        return [n for n in self.slots if n is not None]

    def is_isometric(self) -> bool:
        """Warunek izometrii: długość sznura zawsze równa 48."""
        return len(self.slots) == LENGTH

    def neighbor(self, index: int, offset: int = 1):
        """Sąsiad w domkniętym cyklu (brzeg domknięty)."""
        n = len(self.slots)
        return self.slots[(index + offset) % n]

    def __len__(self):
        return LENGTH

    def __iter__(self):
        return iter(self.slots)

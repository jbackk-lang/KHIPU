"""
rope48.py — ROPE48: sznur pojedynczego CPU w architekturze TETRAGON_4CPU
(MODEL_TETRAGON_4CPU.md, RESONANCE_COMM.md).

    4 warstwy x 12 pozycji = 48 węzłów
    długość sznura = 48 (stała, izometria zachowana)
    brzeg domknięty (cykl)
"""

from typing import List, Optional
from .node256 import Node256

LAYERS = 4
POSITIONS_PER_LAYER = 12
LENGTH = LAYERS * POSITIONS_PER_LAYER  # 48


class Rope48:
    """
    Cykliczny sznur o STAŁEJ długości 48 (izometria warunku brzegowego).
    Sloty puste (jeszcze nieustawione) mają wartość None.
    """

    def __init__(self, name: str):
        self.name = name
        self.slots: List[Optional[Node256]] = [None] * LENGTH

    def set(self, layer: int, position: int, node: Node256) -> None:
        if not (0 <= layer < LAYERS):
            raise ValueError(f"layer poza zakresem [0,{LAYERS - 1}]: {layer}")
        if not (0 <= position < POSITIONS_PER_LAYER):
            raise ValueError(f"position poza zakresem [0,{POSITIONS_PER_LAYER - 1}]: {position}")
        self.slots[layer * POSITIONS_PER_LAYER + position] = node

    def get(self, layer: int, position: int) -> Optional[Node256]:
        return self.slots[layer * POSITIONS_PER_LAYER + position]

    def push(self, node: Node256) -> None:
        """Dokłada węzeł na pierwszy wolny slot (kolejność czasowa)."""
        for i, slot in enumerate(self.slots):
            if slot is None:
                self.slots[i] = node
                return
        raise OverflowError(
            f"Rope48 '{self.name}' jest pełny (izometria: dokładnie {LENGTH} węzłów)."
        )

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

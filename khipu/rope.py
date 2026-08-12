"""
rope.py (w pakiecie khipu) — ROPE256: globalny sznur węzłów NODE256
(modelPC.md / ROPE_MEMORY, MODEL_PC_MEMORY.md, MODEL_PC_TOPLOGIC.md).

Sznur w kolejności czasowej + relacje globalne (odległości, sprzężenia,
rezonanse, przejścia warstw) + walidacja globalna (zgodność S/K, spójność
przebiegu). W przeciwieństwie do ROPE48 (patrz rope48.py) długość ROPE256
nie jest ograniczona do stałej izometrii — rośnie wraz z przetwarzanymi
słowami danych.

Uwaga: to jest inny moduł niż `rope.py` w katalogu głównym repozytorium
(prosty format CTX/NODE do zapisu tekstowego) — ten tutaj to "sznur" jako
struktura danych działającego pipeline'u, tamten to legacy serializacja.
"""

from typing import List
from .node256 import Node256


class Rope256:
    def __init__(self):
        self.nodes: List[Node256] = []

    def append(self, node: Node256) -> None:
        self.nodes.append(node)

    def __len__(self):
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes)

    def __getitem__(self, i):
        return self.nodes[i]

    def screw_sequence(self):
        return [n.s for n in self.nodes]

    def direction_sequence(self):
        return [n.k for n in self.nodes]

    def is_direction_consistent(self) -> bool:
        """Walidacja globalna: każdy węzeł ma K zgodne z regułą DERIVE_DIRECTION(S)."""
        return all(n.is_consistent() for n in self.nodes)

    def layer_transitions(self) -> int:
        """Liczba przejść między warstwami L wzdłuż sznura."""
        count = 0
        for a, b in zip(self.nodes, self.nodes[1:]):
            if a.l != b.l:
                count += 1
        return count
